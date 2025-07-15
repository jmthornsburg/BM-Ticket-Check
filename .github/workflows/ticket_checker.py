name: Check for Tickets

on:
  schedule:
    # Runs the script every 15 minutes
    - cron: '*/15 * * * *'
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests beautifulsoup4

      - name: Run the script
        env:
          MAX_PRICE: ${{ vars.MAX_PRICE }}
          NTFY_TOPIC: ${{ secrets.NTFY_TOPIC }}
        run: python ticket_checker.py
