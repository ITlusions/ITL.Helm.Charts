# itlusions-hellowrld

Minimale hello world chart. Rendert een ConfigMap met de waarde `message`.

Deze chart dient als end-to-end testcase voor de CI-pipeline.

## Waarden

| Naam | Type | Standaard | Beschrijving |
|------|------|-----------|--------------|
| `message` | string | `Hallo, wereld!` | Tekst in de ConfigMap. |
