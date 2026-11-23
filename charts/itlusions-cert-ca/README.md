# ITlusions internal CA

Standalone Helm chart that creates a root CA and separate database-client and workload
intermediate CAs using cert-manager. It does not install cert-manager or require chart dependencies
or a Git submodule. The chart is based on
[ITL.CertManager.CA](https://github.com/ITlusions/ITL.CertManager.CA) at commit
`a415084756a0bdd9502506250b42736561d98f6e`.

See the [PKI hierarchy](docs/1-overview/1.1-pki-hierarchy.md) for the trust chain, issuer usage, verification and
security considerations.

## Prerequisites

- Helm, kubectl, and a Kubernetes cluster with cert-manager installed and its CRDs and webhook ready.
- Deploy into cert-manager's cluster resource namespace, normally `cert-manager`. ClusterIssuer
  CA secrets are resolved in that namespace.
- The Helm identity must be able to read Certificates in that namespace for the legacy migration
  guard.

## Build and inspect

From the repository directory:

```powershell
helm lint .\charts\itlusions-cert-ca
helm template itlusions-ca .\charts\itlusions-cert-ca --namespace cert-manager
python -m unittest discover -s charts\itlusions-cert-ca\tests
```

The chart sets ITlusions-specific CA subjects and secret and intermediate issuer names in
[`values.yaml`](values.yaml). Review these settings before installation.

## Deploy and verify

After confirming the active Kubernetes context and prerequisites:

```powershell
kubectl config current-context
helm upgrade --install itlusions-ca .\charts\itlusions-cert-ca --namespace cert-manager --wait --timeout 10m
kubectl get certificate -n cert-manager
kubectl get clusterissuer
```

Check that the root and intermediate Certificates and the two intermediate ClusterIssuers are
`Ready=True`. Applications should reference `itlusions-database-client-ca-issuer` or
`itlusions-workload-ca-issuer` according to their trust boundary. Clients must separately trust the
root certificate; installing an issuer alone does not distribute trust.

The optional `trustBundle.enabled` value creates a trust-manager Bundle for the public root.
The `keycloak-oidc` kind profile enables it after installing trust-manager. See
[trust distribution](docs/1-overview/1.2-trust-distribution.md) for namespace selection,
permissions, application integration and CA rotation considerations.

The chart uses fixed `itlusions-root-ca-bootstrap-issuer`, `itlusions-root-ca-issuer` and
`itlusions-root-ca` resource names. **Do not install another release owning those resources.**
The post-install/upgrade job reads and patches the CA Secrets for CNPG compatibility. Those
Secrets contain private keys: restrict access and plan backups and rotation.

## Migration from the earlier wrapper

The earlier wrapper created `itl-root-ca`, `itl-root-ca-bootstrap-issuer` and
`itl-root-ca-issuer`, as well as `itl-itlusions-*` intermediate Certificates. This chart renames
those resources while retaining the default CA Secret and intermediate ClusterIssuer names.
Renaming a Certificate or its issuer can trigger reissuance or replacement of a CA key: keeping
the Secret name alone does **not** guarantee the original trust chain.

Do not upgrade an existing installation until you have a tested, secure backup and a migration
plan for CA keys, certificate reissuance, client trust and rollback. A Helm server-connected
install or upgrade fails if the old `itl-root-ca` Certificate is owned by the release or points
at this chart's configured root Secret. Offline `helm template` and client-only dry runs cannot
perform this live check. This guard is not a migration procedure and does not check every possible
custom legacy configuration. For a disposable cluster, recreate it deliberately instead; its old
CA and any certificates or client trust tied to it will be lost or need replacement.

Deleting, replacing, or rotating a CA can break existing trust. The optional bundle distributes
public trust inside Kubernetes, but this chart does not implement a CA rotation procedure.
