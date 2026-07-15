# Fixture: a Cloudflare zone managed in Terraform with three modern-hygiene gaps.
# All identifiers are placeholders.

resource "cloudflare_zone" "example" {
  account_id = "REPLACE_ACCOUNT_ID"
  zone       = "example.com"
}

# SSL/TLS mode Full (non-strict): encrypts the origin leg but does NOT validate
# the origin certificate, so the origin leg is MITM-able. Only Full (strict)
# validates the cert.
resource "cloudflare_zone_settings_override" "example" {
  zone_id = cloudflare_zone.example.id

  settings {
    ssl = "full"
  }
}

# Legacy Page Rule: Page Rules entered maintenance mode on 2025-01-06 and should
# be migrated to Cache/Configuration/Origin/Redirect Rules.
resource "cloudflare_page_rule" "cache_static" {
  zone_id  = cloudflare_zone.example.id
  target   = "example.com/static/*"
  priority = 1

  actions {
    cache_level = "cache_everything"
  }
}

# NOTE: DNSSEC is not enabled for this managed zone (no DNSSEC resource).
