# itlusions-headscale-ui

Headplane, de beheer-webUI voor [itlusions-headscale](../itlusions-headscale/README.md).

Volledige documentatie: [4.8 itlusions-headscale-ui](../../docs/4-beheer-en-toegang/4.8-itlusions-headscale-ui.md).

## Installatie

```powershell
helm upgrade --install itlusions-headscale-ui .\charts\itlusions-headscale-ui --namespace itlusions-headscale-ui --create-namespace --set adminAllowedCIDRs[0]=<cidr>
```

## Vereiste secrets

- `headplane-oidc-secret` en `headplane-cookie-secret`: worden door de chart gegenereerd (`secrets.manage: true`).
- `headplane-headscale-api-key`: zelf aanmaken met `headscale apikeys create`, nadat itlusions-headscale draait.

## Belangrijkste waarden

| Waarde | Doel |
|---|---|
| `route.hostname` | Hostnaam van Headplane. |
| `adminAllowedCIDRs` | Bron-CIDR's die toegang krijgen. Leeg blokkeert alles. |
| `headscale.url`, `headscale.publicUrl` | Headscale-endpoints. |

## Testen

```powershell
helm lint .\charts\itlusions-headscale-ui
helm template itlusions-headscale-ui .\charts\itlusions-headscale-ui --set adminAllowedCIDRs[0]=10.0.0.0/8
```
