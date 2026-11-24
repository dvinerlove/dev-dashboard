# 61 — pier IdentifyInfra.swift (infra/service detection source)

- URL: https://github.com/StepanBlaha/pier/blob/main/Sources/PierCore/Identify/IdentifyInfra.swift (raw)
- Title: IdentifyInfra.swift — well-known service detection rules
- Publisher: GitHub / Štěpán Bláha (official source code)
- Tier: L1 | Source class: vendor-authored | Fetched: 2026-11-24

## Key quotes
- InfraRule fields: names (exact proc/executable basenames), argFragments (argv substrings for JVM/beam), pathFragments (exe path), ports, dockerPorts ("identify the service only when proxied by docker/orbstack"), nonHTTP, httpPorts.
- Rules: PostgreSQL 5432, Redis 6379, MongoDB 27017, MySQL 3306, Memcached 11211, Ollama 11434, Elasticsearch 9200, RabbitMQ 5672/15672, Kafka 9092, ClickHouse 8123, Meilisearch 7700, NATS 4222, MinIO (dockerPorts 9000/9001), Supabase (dockerPorts 54321-4), Mailpit 8025/1025...
- dockerPrefixes = ["docker", "com.docker", "vpnkit", "orbstack", "colima", "limactl"]
- Priority: "Name match beats port match. Port-only matches are skipped for processes that look like someone's dev server (project cwd, JS/Python runtime, known framework), unless docker-proxied."
