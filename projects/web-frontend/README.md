# GCOM Front-End 2024

## Description

GCOM UI to interact with GCOM Back-End and MissionPlanner Scripts. Built with Vite, React + Redux, MUI, and Typescript. Communication is achieved through axios http and ~~socket.io v4 websockets.

CSS is done through inline styling with MUI components. More info can be found [below](#useful-links).

_Project Link: https://github.com/orgs/ubcuas/projects/6/views/5_

## Development Setup
Node.js v20 is required for development, download at https://nodejs.org/en/download/current or use `nvm` if you're cool and swag with it.
### Steps:
1. Navigate to project directory and run `npm i` to install required libraries.
```
cd projects/web-frontend
npm i
```
2. `npm run dev` to start the app in development mode.
```
npm run dev
```
### Video stream
The `/webrtc-test` page shows a camera stream from MediaMTX. It uses two optional settings in `.env`:

- `VITE_MEDIAMTX_URL`: where MediaMTX is running (default `http://localhost:8889`)
- `VITE_MEDIAMTX_STREAM`: which stream to show, as named in `docker/mediamtx.yml` (default `test`)

See the [MediaMTX README](../../docker/README.md) for starting MediaMTX and publishing a test stream.

## Useful Links
- MUI Component Reference - https://mui.com/material-ui/getting-started/
- Socket.io Reference - https://socket.io/docs/v4/
- GCOM Back-End Repository - https://github.com/ubcuas/GCOM-2023
- React Docs - https://react.dev/reference/react


### Offline Maps

OFFLINE MAPPING - PLEASE TAKE A LOOK AT https://github.com/orgs/ubcuas/projects/6?pane=issue&itemId=42266000 FOR FULL INSTRUCTIONS ON HOW TO SETUP OFFLINE MAPPING WITH FRONT END, SKIP TO STEP 4 BECAUSE HOPEFULLY I'LL HAVE DONE ALL OF THE TILE DATA PREPPING. Or DM @suubwey in discord.
