# noip-renew

Small Python utility to log in to No-IP, complete TOTP-based 2FA, inspect DNS records, and confirm hosts that are close to expiration.

## What it does

`main.py`:

- logs in to `https://www.noip.com/login`
- submits a TOTP 2FA code
- opens the No-IP DNS records page
- checks whether any host requires manual confirmation
- confirms the host when required
- logs out

## Requirements

- Python 3.10+ recommended
- A No-IP account
- No-IP TOTP 2FA enabled
- Your No-IP TOTP secret

## Environment variables

Create a `.env` file in the project root. You can copy from `.env-example`.

```env
NOIP_USERNAME=your@email.com
NOIP_PASSWORD=your_password
NOIP_TOTP_SECRET=YOUR_TOTP_SECRET
```

Variable meaning:

- `NOIP_USERNAME`: No-IP login email or username
- `NOIP_PASSWORD`: No-IP account password
- `NOIP_TOTP_SECRET`: secret key used to generate the 2FA code

## Install and run

### Windows

```bat
renew.bat
```

### Linux / macOS

```bash
chmod +x renew
./renew
```

Both launcher scripts:

- create `.venv` if it does not exist
- upgrade `pip`
- install packages from `requirement.txt`
- run `python main.py`

## Auto-confirm mode

By default, the script prompts before confirming a host that needs renewal.

To skip the prompt and confirm automatically:

```bash
python main.py --auto-renew
```

PowerShell:

```powershell
python .\main.py --auto-renew
```

## Manual setup

If you do not want to use the launcher scripts:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirement.txt
python main.py
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\requirement.txt
python .\main.py
```

## Files

- `main.py`: renewal workflow
- `renew`: Bash launcher
- `renew.bat`: Windows launcher
- `.env-example`: environment template
- `requirement.txt`: Python dependencies

## Notes

- The script only sends a confirmation request when No-IP shows a host needs confirmation.
- The current implementation confirms the first matching host it finds on the records page.
- In interactive mode, choosing anything other than `y` skips confirmation.
- `renew.bat` pauses at the end so the terminal window stays open.

## Expected output

Typical success flow:

```text
⌛ Logging in as your@email.com ...
⌛ Verifying code ...
✅ Login successful
⌛ Pulling records
✅ Pulling successful
⌛ Confirming: your-host.example.com
✅ Confirm sussessul
✅ Logout successful
```
