# Acquiring the RSTGCN dataset

Use this procedure only after written permission is retained locally. The script downloads
the archive from the authors' public GitHub repository, calculates SHA-256, extracts it
to ignored local storage, and records retrieval metadata.

```powershell
.\scripts\acquire_rstgcn.ps1
```

It refuses to run into a non-empty destination, preventing accidental overwrite. Do not
commit `data/raw/`, archive files, or the generated local provenance manifest.

After acquisition, run the no-Snowflake validation preflight:

```powershell
.\scripts\preflight_rstgcn.ps1
```
