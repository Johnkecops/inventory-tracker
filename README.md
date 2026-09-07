# 💊 Drug Tracking System

A Streamlit app for a small pharmacy: register patients, keep a drug inventory,
and record dispensing against live stock. Reads render with `st.dataframe`;
writes go through `st.form` submissions into MySQL stored procedures, so stock
reduction and expiry checks happen in the database rather than in the UI.

Four views: purchase-history dashboard, patient management, drug inventory, and
purchase recording (restricted to drugs that are in stock and unexpired).

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Start MySQL

   The app needs a MySQL server listening on port 3306. On macOS with Homebrew:

   ```
   $ brew services start mysql          # persists across reboots
   $ /opt/homebrew/opt/mysql/bin/mysql.server start   # this session only
   ```

   If you skip this step the app reports
   `Can't connect to MySQL server on 'localhost' ([Errno 61] Connection refused)`.

3. Create the database

   ```
   $ /opt/homebrew/opt/mysql/bin/mysql -u root < schema.sql
   ```

   Use the server's own client, not whatever `mysql` resolves to on your PATH.
   A Conda or system MySQL 5.7 client cannot authenticate against a MySQL 8+
   server using `caching_sha2_password` and fails with an auth-plugin error.
   Add `-p` if your `root` account has a password; a Homebrew install has none
   by default.

   `schema.sql` is reconstructed from the queries the app issues, not exported
   from a production instance. Check it against your own database before relying
   on it.

4. Point the app at your MySQL server

   Copy the example secrets file and fill in your credentials:

   ```
   $ mkdir -p .streamlit && cp secrets.toml.example .streamlit/secrets.toml
   ```

   `.streamlit/secrets.toml` is gitignored. Without it the app falls back to
   `root@localhost` with an empty password on database `DrugTrackingSystem`.

5. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```
**Note**: This streamline app hasn’t been tested on linux and windows. So some adjustments are needed as homebrew package manager is working only for Linux and macOS. If you are windows user, you might need to install WSL first before using Homebrew.

**AI Assistance Disclaimer**: This codebase was developed with the assistance of Claude Code. While the AI provided code generation, debugging, and structural support, the human developer maintains full responsibility for reviewing, testing, and maintaining all content and functionality.