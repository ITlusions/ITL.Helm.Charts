# itlusions-headscale

Headscale-besturingsserver voor het ITlusions-mesh-VPN, met Keycloak OIDC. De beheer-UI staat in [itlusions-headscale-ui](../itlusions-headscale-ui/README.md).

Volledige documentatie: [4.7 itlusions-headscale](../../docs/4-beheer-en-toegang/4.7-itlusions-headscale.md).

## Installatie

```powershell
helm upgrade --install itlusions-headscale .\charts\itlusions-headscale --namespace itlusions-headscale --create-namespace
```

## Vereiste secrets

- `headscale-oidc-secret`: wordt door de chart gegenereerd (`secrets.manage: true`).
- `subnet-router-authkey` (alleen met `subnetRouter.enabled: true`): zelf aanmaken met `headscale preauthkeys create`.

## Belangrijkste waarden

| Waarde | Doel |
|---|---|
| `serverUrl`, `route.hostname` | Publieke hostnaam van Headscale. |
| `adminAllowedCIDRs` | Bron-CIDR's voor `/swagger`. Leeg blokkeert alles. |
| `oidc.allowedGroups` | Groepen die mogen inloggen. |
| `subnetRouter.enabled`, `advertiseRoutes` | Subnet router; standaard uit. |

## Testen

```powershell
helm lint .\charts\itlusions-headscale
helm template itlusions-headscale .\charts\itlusions-headscale
```
