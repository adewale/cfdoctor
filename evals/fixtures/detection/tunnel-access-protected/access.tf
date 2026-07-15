# A Cloudflare Access application protects the tunnel hostname, so
# CFDOC-SEC-TUNNEL-NO-ACCESS must be suppressed. Placeholders only.

resource "cloudflare_zero_trust_access_application" "admin" {
  account_id = "REPLACE_ACCOUNT_ID"
  name       = "Admin"
  domain     = "admin.example.com"
}

resource "cloudflare_zero_trust_access_policy" "admin_team" {
  account_id     = "REPLACE_ACCOUNT_ID"
  application_id = cloudflare_zero_trust_access_application.admin.id
  name           = "Allow team"
  decision       = "allow"

  include {
    email_domain = ["example.com"]
  }
}
