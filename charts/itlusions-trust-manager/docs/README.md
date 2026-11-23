# ITlusions trust-manager

Documentation for the [itlusions-trust-manager chart](../).

## What do cert-manager and trust-manager do?

**cert-manager issues and renews certificates. trust-manager distributes the public CA
certificates that applications need to trust those certificates.**

cert-manager uses a `Certificate` to request a certificate from an `Issuer` or
`ClusterIssuer`, such as an internal CA or Let's Encrypt. The issued certificate and its
private key are stored in a Kubernetes Secret.

trust-manager uses a `Bundle` to collect public CA certificates from one or more sources
and synchronize them to selected namespaces. It does not issue certificates.

## ITlusions configuration

The trust-manager chart installs trust-manager as a separate release after cert-manager.
The separate ITlusions CA chart can then create the `itlusions-internal-trust` Bundle. The
`keycloak-oidc` profile enables that Bundle:

1. The Bundle reads the public root from the `tls.crt` key of the
   `cert-manager/itlusions-root-ca` Secret.
2. trust-manager writes the root to the `ca.crt` key of the `itlusions-internal-trust`
   ConfigMap in the selected `cert-manager`, `keycloak`, and `operators` namespaces.
3. When the source changes, trust-manager resynchronizes the ConfigMaps.

```text
cert-manager                         trust-manager

ITlusions root-CA Secret              Bundle: itlusions-internal-trust
  |-- tls.key  (private key)           |
  `-- tls.crt  (public root) ----------+
                                       |-- ConfigMap in cert-manager
                                       |-- ConfigMap in keycloak
                                       `-- ConfigMap in operators
```

The private key is **not** copied to the ConfigMaps. The trust-manager controller can,
however, read Secrets in its trust namespace, including private keys. Restrict access to
the controller and review its permissions for production.

## Using the trust bundle

A ConfigMap does not automatically make an application trust the CA. An application must
load `ca.crt` itself and might need a restart or truststore reload. Browsers, host tools,
and the Kubernetes API server need a separate way to trust the public root.

The ITlusions Bundle contains only the internal root by default. Applications verifying a
Let's Encrypt certificate typically use their existing public truststore. Public CAs can
optionally be added to the Bundle; see the separate ITlusions CA chart documentation.

## Documentation

| Group | Document | Topic |
|---|---|---|
| 1 Overview | [1.1](1-overview/1.1-trust-manager.md) | Installation, Bundle integration, and security |
| | [1.2](1-overview/1.2-namespace-selection.md) | Selecting and verifying target namespaces |
