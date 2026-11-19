# Setting up "Continue with Google"

Google needs to know about the site before it lets people sign in to it. You create a free "OAuth client" once, and put its two values in `.env`. About 10 minutes.

1. Go to <https://console.cloud.google.com/> and sign in with your Google account.
2. **Create a project:** project picker at the top → *New project* → name it `Cumetria` → *Create*. Make sure it's selected.
3. **Consent screen** (what people see when they click the button): *APIs & Services → OAuth consent screen* (in newer consoles: *Google Auth Platform → Branding*).
   - App name: `Cumetria`. Support email: yours.
   - Audience / user type: **External**.
   - Scopes: only the basic ones (`email`, `profile`, `openid`); those don't need a review by Google.
   - Publish the app (*Audience → Publish app*), otherwise only accounts you add as "test users" can sign in.
4. **Create the client:** *APIs & Services → Credentials → Create credentials → OAuth client ID*.
   - Application type: **Web application**. Name: `Cumetria`.
   - **Authorized redirect URIs**, add both:
     - `http://localhost:8080/accounts/google/login/callback/` (your PC)
     - `https://YOUR-DOMAIN/accounts/google/login/callback/` (the server, once you have the domain)
   - *Create*.
5. Copy the **Client ID** and **Client secret** into `.env`:
   ```
   GOOGLE_CLIENT_ID=....apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=....
   ```
6. Restart: `docker compose up --build`. The login page now shows *Continue with Google*.

Keep the secret private: it only goes in `.env`, which is never committed.

Google's console changes its menus from time to time; if a name above doesn't match, the steps are the same in spirit: project, consent screen, web OAuth client with the redirect URIs.
