# Fixture: SSL/TLS mode Off (worst case, graded high) but DNSSEC is enabled, so
# the DNSSEC-missing lead must be suppressed. All identifiers are placeholders.

resource "cloudflare_zone" "example" {
  account_id = "REPLACE_ACCOUNT_ID"
  zone       = "insecure.example"
}

# DNSSEC is enabled for this zone, so CFDOC-CONFIG-DNSSEC-MISSING must not fire.
resource "cloudflare_zone_dnssec" "example" {
  zone_id = cloudflare_zone.example.id
}

# SSL/TLS mode Off: no encryption to the origin at all. Graded high, same as
# Flexible. This is NOT Full (non-strict).
resource "cloudflare_zone_settings_override" "example" {
  zone_id = cloudflare_zone.example.id

  settings {
    ssl = "off"
  }
}
