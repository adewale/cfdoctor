# Intentional status route

This is a dedicated status endpoint. The exact route `example.com/api/status` is intentional: production health checks never add query parameters, and requests for every other URL must stay on the origin rather than invoke this Worker. Responses deliberately use `Cache-Control: no-store` so each health check executes current code. `workers_dev` is disabled, observability is sampled, and there are no account-managed bindings for this Worker.
