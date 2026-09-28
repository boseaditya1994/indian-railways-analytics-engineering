# Snowflake connection

The local `.env` contains account identifier, username, role, and non-secret defaults only.
It is ignored by Git. This account uses native Snowflake authentication: the preflight
prompts for the password locally via hidden terminal input. No password, private key,
token, or MFA code is stored in the repository.

Run the read-only preflight before project setup:

```powershell
.\.venv\Scripts\python.exe .\scripts\snowflake_preflight.py
```

Enter the password only into the hidden local prompt. The script reports active account,
user, role, warehouse, and whether `COMPUTE_WH` exists. It creates nothing.
