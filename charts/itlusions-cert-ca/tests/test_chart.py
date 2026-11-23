import re
import subprocess
import tempfile
import unittest
from pathlib import Path


CHART = Path(__file__).resolve().parents[1]


def render(*overrides):
    result = subprocess.run(
        ['helm', 'template', 'itlusions-cert-ca', str(CHART), '--namespace', 'cert-manager', *overrides],
        capture_output=True, text=True, check=True,
    )
    resources = {}
    for document in re.split(r'^---\s*$', result.stdout, flags=re.MULTILINE):
        kind = re.search(r'^kind: (\S+)$', document, re.MULTILINE)
        name = re.search(r'^metadata:\s*\n\s+name: "?([^"\s]+)"?', document, re.MULTILINE)
        if kind and name:
            key = kind.group(1), name.group(1)
            if key in resources:
                raise AssertionError(f'Duplicate rendered resource: {key}')
            resources[key] = document
    return resources


class ChartTests(unittest.TestCase):
    def test_default_hierarchy(self):
        resources = render()
        expected = {
            ('Certificate', 'itlusions-root-ca'),
            ('Certificate', 'itlusions-database-client-ca'),
            ('Certificate', 'itlusions-workload-ca'),
            ('ClusterIssuer', 'itlusions-root-ca-bootstrap-issuer'),
            ('ClusterIssuer', 'itlusions-root-ca-issuer'),
            ('ClusterIssuer', 'itlusions-database-client-ca-issuer'),
            ('ClusterIssuer', 'itlusions-workload-ca-issuer'),
            ('ServiceAccount', 'itlusions-cert-ca-ca-key-compat'),
            ('Role', 'itlusions-cert-ca-ca-key-compat'),
            ('RoleBinding', 'itlusions-cert-ca-ca-key-compat'),
            ('Job', 'itlusions-cert-ca-ca-key-compat'),
        }
        self.assertEqual(set(resources), expected)
        for purpose in ('root', 'database-client', 'workload'):
            certificate = resources['Certificate', f'itlusions-{purpose}-ca']
            issuer = 'itlusions-root-ca-bootstrap-issuer' if purpose == 'root' else 'itlusions-root-ca-issuer'
            duration = '87600h' if purpose == 'root' else '43800h'
            self.assertIn('  isCA: true', certificate)
            self.assertIn(f'  duration: "{duration}"', certificate)
            self.assertIn(f'  secretName: "itlusions-{purpose}-ca"', certificate)
            self.assertIn(f'    name: {issuer}', certificate)
            self.assertIn('    algorithm: ECDSA\n    size: 256', certificate)
        for purpose in ('database-client', 'workload'):
            issuer = resources['ClusterIssuer', f'itlusions-{purpose}-ca-issuer']
            self.assertIn(f'    secretName: "itlusions-{purpose}-ca"', issuer)
        self.assertIn('    secretName: "itlusions-root-ca"',
                      resources['ClusterIssuer', 'itlusions-root-ca-issuer'])
        self.assertIn('  selfSigned: {}', resources['ClusterIssuer', 'itlusions-root-ca-bootstrap-issuer'])

    def test_configured_secrets_are_used_by_issuers_and_compatibility_job(self):
        with tempfile.TemporaryDirectory() as directory:
            values = Path(directory) / 'values.yaml'
            values.write_text(
                'intermediates:\n'
                '  - name: database-client\n'
                '    commonName: Client CA\n'
                '    organization: [ITlusions]\n'
                '    country: [NL]\n'
                '    duration: 43800h\n'
                '    secretName: custom-client\n'
                '    issuerName: itlusions-database-client-ca-issuer\n'
                '  - name: workload\n'
                '    commonName: Workload CA\n'
                '    organization: [ITlusions]\n'
                '    country: [NL]\n'
                '    duration: 43800h\n'
                '    secretName: itlusions-workload-ca\n'
                '    issuerName: itlusions-workload-ca-issuer\n',
                encoding='utf-8',
            )
            resources = render('--set', 'root.secretName=custom-root', '--values', str(values))
        self.assertIn('  secretName: "custom-root"', resources['Certificate', 'itlusions-root-ca'])
        self.assertIn('    secretName: "custom-root"', resources['ClusterIssuer', 'itlusions-root-ca-issuer'])
        self.assertIn('  secretName: "custom-client"', resources['Certificate', 'itlusions-database-client-ca'])
        self.assertIn('    secretName: "custom-client"',
                      resources['ClusterIssuer', 'itlusions-database-client-ca-issuer'])
        role = resources['Role', 'itlusions-cert-ca-ca-key-compat']
        self.assertIn('resourceNames: ["custom-root", "custom-client", "itlusions-workload-ca"]', role)
        job = resources['Job', 'itlusions-cert-ca-ca-key-compat']
        self.assertIn('"helm.sh/hook": post-install,post-upgrade', job)
        self.assertIn('for secret in custom-client itlusions-workload-ca', job)

    def test_trust_bundle_is_opt_in_and_distributes_only_public_root(self):
        self.assertNotIn(('Bundle', 'itlusions-internal-trust'), render())
        resources = render('--set', 'trustBundle.enabled=true',
                           '--set', 'root.secretName=custom-root')
        bundle = resources['Bundle', 'itlusions-internal-trust']
        self.assertIn('        name: "custom-root"', bundle)
        self.assertIn('        key: tls.crt', bundle)
        self.assertIn('      key: ca.crt', bundle)
        self.assertIn('      - key: kubernetes.io/metadata.name', bundle)
        for namespace in ('cert-manager', 'keycloak', 'operators'):
            self.assertIn(f'        - {namespace}', bundle)
        self.assertNotIn('useDefaultCAs:', bundle)
        self.assertNotIn('tls.key', bundle)
        public = render('--set', 'trustBundle.enabled=true',
                        '--set', 'trustBundle.includePublicCAs=true',
                        '--set', 'trustBundle.additionalSources[0].secret.name=old-root',
                        '--set', 'trustBundle.additionalSources[0].secret.key=tls.crt')
        public_bundle = public['Bundle', 'itlusions-internal-trust']
        self.assertIn('    - useDefaultCAs: true', public_bundle)
        self.assertIn('        name: old-root', public_bundle)
        self.assertIn('        key: tls.crt', public_bundle)

    def test_trust_bundle_namespace_scope_is_explicit(self):
        labels = render('--set', 'trustBundle.enabled=true',
                        '--set-string', r'trustBundle.namespaceSelector.matchLabels.itlusions\.io/trust=true')
        label_bundle = labels['Bundle', 'itlusions-internal-trust']
        self.assertIn('itlusions.io/trust: "true"', label_bundle)
        self.assertNotIn('kubernetes.io/metadata.name', label_bundle)
        for override, message in (
                ('trustBundle.namespaces=[]', 'trustBundle.namespaces must not be empty'),
                ('trustBundle.namespaceSelector.matchExpressions=[]',
                 'trustBundle.namespaceSelector must contain matchLabels or matchExpressions')):
            with self.subTest(override=override):
                args = ['helm', 'template', 'itlusions-cert-ca', str(CHART),
                        '--set', 'trustBundle.enabled=true']
                if override.startswith('trustBundle.namespaceSelector'):
                    args += ['--set-json', 'trustBundle.namespaces=[]']
                result = subprocess.run(
                    [*args, '--set-json', override],
                    capture_output=True, text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)


if __name__ == '__main__':
    unittest.main()
