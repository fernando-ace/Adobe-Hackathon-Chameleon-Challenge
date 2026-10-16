# Offline Docker validation

Revalidated after the tall-format CTA/badge scale cap and portrait-band spacing adjustment on 2026-10-16 with Docker Desktop 4.77.0 and engine 29.5.3.

Build for the challenge architecture:

```powershell
docker build --platform linux/amd64 -t chameleon-engine .
```

The build succeeded. `Dockerfile` leaves platform selection to the command-line flag, avoiding Docker's redundant `FROM --platform` warning.

Offline run:

```powershell
docker run --rm --network none `
  -v "${PWD}/input:/app/input" `
  -v "${PWD}/evidence/docker:/app/output" `
  chameleon-engine
```

Two consecutive runs completed with `OK`, and the repository validator reported zero issues for every output:

- Level 1: 0.14–0.21 s; PNG 107,497 bytes
- Level 2: 0.21–0.23 s; PNG 69,531 bytes
- Level 3: 0.32–0.37 s; PNG 43,235 bytes

Two consecutive `--network none` runs produced byte-identical JSON and PNG
outputs for all three official samples. PNG SHA-256 values: Level 1
`a1a27605f6fbf2a771896e0ff24179040a3d676796c7daf68cdd99edc0a6b095`, Level 2
`871654b7992f5d38acca64e8481ac52da6dad0900f8922d9dac359c65d81cf54`, Level 3
`820ffb3ae06d4d1ab59bb70a7b1feafb4d03544d7922d8299ef15d95798bf129`.

The generated JSON retained source element IDs and counts, text content, and font families. Output geometry stayed within each target canvas. Contain-fit images retained their source frame ratios; cover-fit backgrounds use a target-sized frame by design. The only warning on the offline run was Fontconfig's non-fatal `05-reset-dirs-sample.conf` warning.

To recover Docker Desktop after an unclean shutdown, this host had orphaned Windows socket reparse points in both `%LOCALAPPDATA%\Docker\run` and `%LOCALAPPDATA%\docker-secrets-engine`. Direct socket deletion failed with Windows error 1920. Renaming the socket-only runtime directories aside let Docker recreate them; Docker then answered `docker info` and ran the offline image. The preserved directories are outside the repository.
