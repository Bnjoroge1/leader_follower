# DevNotes

Lightweight web application to help developers keep track of their notes in an organized manner. Created by Dhilan Patel for Object Oriented Software Engineering (SP25).

## Installing / Getting started

1. Clone this [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) repository

2. Make sure the latest versions of [Node.js](https://nodejs.org/) and [pnpm](https://pnpm.io/) are installed systemwide.

3. Create `.env` file in `/web` directory with the following code:

```env
VITE_API_URL=http://localhost:3000
```

4. Navigate to the root directory `homework-dhilanpatel26` in two separate terminals and execute the following commands to install the necessary dependencies and start the app:
```shell
cd api && pnpm install && pnpm dev
```
```shell
cd web && pnpm install && pnpm dev
```

5. Navigate to the DevNotes homepage at `http://localhost:5173` in any web browser.

Note that at this time many CRUD operations will be unauthorized since the user is not authenticated.

## Developing

Detailed and step-by-step documentation for setting up local development. For example, a new team member will use these instructions to start developing the project further. 

1. Create GitHub OAuth Application:
    - Go to GitHub Settings > Developer Settings > OAuth Apps > New OAuth App
    - Set Application name to whatever you want (e.g. DevNotes)
    - Set Homepage URL: `http://localhost:3000`
    - Set Authorization callback URL: `http://localhost:3000/login/github`
    - Copy your Client ID and Client Secret

2. Create `.env` file in `/api` directory with the following code:

```env
GITHUB_CLIENT_ID=your_client_id_here
GITHUB_CLIENT_SECRET=your_client_secret_here
SERVER_URI=http://localhost:3000
NODE_ENV=development
```

3. Navigate to the root directory `homework-dhilanpatel26` and execute the following commands:

```shell
cd api && pnpm dev
cd ../web && pnpm dev
```

4. Navigate to the DevNotes homepage at `http://localhost:5173` in any web browser.

5. Optionally execute the following commands, then navigate to `https://local.drizzle.studio` in any web browser to view the database tables.

```shell
pnpm db:studio
```

## Testing CRUD Operations

### Authenticating
- The following features are only available to authorized users. Click the `Sign in` button to authenticate through GitHub OAuth.

### Creating a note:
- Click the plus icon in the top left corner.
- Enter a title and content for the note (these cannot be empty).
- Click `Save` to save and upload your note to the database, or `Cancel` to cancel note creation.
- Your newly created note is now visible at the top of your feed with the title, content, and date of creation.

### Reading all your notes:
- All your notes will automatically populate your feed in reverse-chronological order by date of creation/last modification.

### Reading notes filtered by a search keyword:
- Click the magnifying glass icon in the top left corner.
- Enter your keyphrase (this is case-insensitive).
- Click `Save` to save your search configuration, `Clear` to clear the textbox, or `Cancel` to cancel your search. 
    - Saving will only show notes whose title or content contain the keyphrase. 
    - In order to return to no search, you must click `Save` after `Clear`.
    - Cancelling will return back to your most recently saved search.

### Updating a note:
- Click the pencil icon in the top right corner of the note you want to edit.
- Edit the title and content field as desired (these cannot be empty).
- Click `Save` to save your new note, or `Cancel` to return your note to its previous state.
- Upon saving a change to your title or content, your note will be updated with the current time of last modification and appear at the top of your feed.
- A note edited while in search mode to no longer satisfy the search criteria is designed to remain in the feed. This is a strategic choice to reduce network traffic and minimize confusion as the note would disappear from view. Re-search to get an updated view of your filtered notes.

### Deleting a note:
- Click the trash can icon in the top right corner of the note you want to delete.
- When the confirmation dialog appears, click the `Confirm` button.


## Tech Stack

### Frontend
- [React](https://react.dev/) v18.3 - UI Library
- [TypeScript](https://www.typescriptlang.org/) v5.6 - Type-safe JavaScript
- [Vite](https://vitejs.dev/) v6.0 - Build tool and dev server
- [Tailwind CSS](https://tailwindcss.com/) v3.4 - Styling framework
- [Nanostores](https://github.com/nanostores/nanostores) v0.11 - State management

### Backend
- [Hono](https://hono.dev/) v4.6 - Lightweight web framework for backend APIs
- [TypeScript](https://www.typescriptlang.org/) v5.6 - Type-safe JavaScript
- [Lucia](https://lucia-auth.com/) v3.2 - Auth library
- [Drizzle ORM](https://orm.drizzle.team/) v0.39 - TypeScript ORM

### Database
- [SQLite](https://www.sqlite.org/) v3 (via better-sqlite3 v11.8) - File-based SQL database

### Development Tools
- [Node.js](https://nodejs.org/) v23.6 - JavaScript runtime environment
- [pnpm](https://pnpm.io/) v10.0 - Package manager
- [Drizzle Kit](https://orm.drizzle.team/kit-docs/overview) v0.30 - Database management tool
- [VSCode](https://code.visualstudio.com/) - Code editor
- [GitHub OAuth](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app) - Authentication
- [Prettier](https://prettier.io/) v3.4 - Code formatter
- [ESLint](https://eslint.org/) v9.17 - Linting tool

### Testing
- [Postman](https://www.postman.com/) - API testing

## Citations
- [FullStack JavaScript Posts App](https://www.madooei.com/coursebooks/fsjs/apps/posts-ui/task-0) - UI and server scaffolding and tech stack inspiration
- [GitHub Copilot](https://github.com/features/copilot) - Debugging and code completion
- [Lucia Documentation](https://github.com/lucia-auth/examples/tree/main/hono/github-oauth) - GitHub OAuth scaffolding and example code




## Assignment Instructions

You should include what is needed (e.g. all of the configurations) to set up the dev environment. For instance, global dependencies or any other tools (include download links), explaining what database (and version) has been used, etc. If there is any virtual environment, local server, ..., explain here. 

Additionally, describe and show how to run the tests, explain your code style and show how to check it.

If your project needs some additional steps for the developer to build the project after some code changes, state them here. Moreover, give instructions on how to build and release a new version. In case there's some step you have to take that publishes this project to a server, it must be stated here. 
