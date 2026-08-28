# VeriDoc Nexus Dashboard Checklist

- [x] Create a portable ZIP of the dashboard source without dependencies or generated logs.
- [x] Validate the ZIP contains the expected frontend source and configuration files.
- [x] Provide local extraction and dependency-install commands.
- [x] Provide the `VITE_VERIDOC_API_URL` configuration step.
- [x] Explain how to run the dashboard and backend together.

## Current Debugging Checklist

- [x] Start and confirm the backend is listening on port 8000; startup succeeded before interruption.
- [x] Confirm `/ask` POST returns HTTP 200 Server-Sent Events.
- [x] Confirm the dashboard uses the correct local port and API URL after `/ask` is verified.
- [ ] Confirm FastAPI allows the dashboard origin through CORS.
- [ ] Fix frontend parsing of the `/ask` Server-Sent Events stream and verify Run research.
