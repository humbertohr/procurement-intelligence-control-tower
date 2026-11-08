# Procurement Intelligence Control Tower

**A multi-agent procurement analytics and decision-support dashboard
powered by CrewAI, Google Gemini, Python, and Streamlit.**

The Procurement Intelligence Control Tower combines supplier performance
analytics, invoice reconciliation, fulfillment-exception monitoring, and
AI-generated management insights in one interactive dashboard.

> **Architecture note:** CrewAI generates the analytical reports in a
> separate analysis workflow. The published Streamlit application reads
> the saved outputs; it does not need to run the CrewAI agents every
> time a visitor opens the dashboard.

## 1. Platform overview

  -----------------------------------------------------------------------
  Workstream                          Purpose
  ----------------------------------- -----------------------------------
  Agent 1 --- Supplier Performance    Evaluates supplier purchasing
                                      activity and delivery reliability.

  Agent 2 --- Financial               Reconciles invoice, payment, and
  Reconciliation                      outstanding-balance information.

  Agent 3 --- Fulfillment Exceptions  Identifies purchase orders without
                                      a corresponding goods-receipt
                                      record and highlights documentation
                                      exceptions.

  Agent 4 --- Executive Intelligence  Synthesizes the analytical outputs
                                      into management observations and
                                      decision-support recommendations.
  -----------------------------------------------------------------------

The Streamlit application also includes deterministic data validation
and methodology.

## 2. How CrewAI connects to the dashboard

The project follows a **prepare → analyze → export → visualize**
workflow.

``` text
Procurement source data
        |
        v
Python / Pandas data preparation
        |
        v
Validated procurement metrics and tables
        |
        +------------------------------+
        |                              |
        v                              v
CrewAI multi-agent workflow       Deterministic validation
        |
        v
Google Gemini language model
        |
        +--> Agent 1: Supplier Performance
        +--> Agent 2: Financial Reconciliation
        +--> Agent 3: Fulfillment Exceptions
        +--> Agent 4: Executive Intelligence
                        |
                        v
                Exported dashboard files
                  dashboard_data.pkl
                  agent_outputs.json
                        |
                        v
                   Streamlit app.py
                        |
                        v
          Procurement Intelligence Control Tower
```

### CrewAI orchestration

CrewAI coordinates specialized agents, each assigned a distinct
analytical responsibility. The first three agents analyze separate
procurement domains. The fourth agent synthesizes their findings into an
executive-level report.

Google Gemini is used as the language model for agent reasoning and
report generation. The Gemini API key should be supplied securely in the
analysis environment (for example, through Google Colab Secrets) and
must never be committed to GitHub.

### Saved outputs

After the agent workflow completes, results are exported for the
dashboard:

-   **`dashboard_data.pkl`** --- structured, deterministic metrics and
    tables used by the Streamlit visualizations.
-   **`agent_outputs.json`** --- saved narrative outputs from the four
    CrewAI agents, including the executive intelligence report.

The Streamlit application loads these files and presents the results.
This separation keeps dashboard viewing independent from the more
expensive and time-consuming AI analysis workflow.

**To refresh the analysis:** rerun data preparation, validation, and the
CrewAI workflow; export updated files; then publish the updated
artifacts with the application.

## 3. Technology stack

-   **Python** --- application and analytical workflow.
-   **Pandas** --- data preparation, aggregation, and reconciliation.
-   **Streamlit** --- interactive dashboard.
-   **Plotly** --- interactive charts.
-   **CrewAI** --- multi-agent orchestration.
-   **Google Gemini** --- language model used by the CrewAI agents.
-   **GitHub** --- source-code and project-version control.
-   **Streamlit Community Cloud** --- dashboard hosting.

## 4. Dashboard sections

1.  **Executive Overview** --- portfolio KPIs and high-level procurement
    exceptions.
2.  **Agent 1: Supplier Performance** --- supplier spend and delivery
    reliability.
3.  **Agent 2: Financial Reconciliation** --- paid and outstanding
    invoices, overdue balances, and supplier-level AP exposure.
4.  **Agent 3: Fulfillment Exceptions** --- sent purchase orders without
    a recorded goods receipt or linked invoice.
5.  **Agent 4: Executive Intelligence** --- AI-generated
    cross-functional observations and management priorities.
6.  **Data Validation & Methodology** --- deterministic checks,
    definitions, and analytical limitations.

## 5. Data and analytical limitations

-   The project dataset is synthetic and intended for demonstration and
    analytical workflow development.
-   The dataset's currency has not been independently verified. Dollar
    signs in the dashboard are a display convention and do not confirm
    that values are denominated in USD.
-   A missing goods-receipt record is a potential fulfillment or
    documentation exception; it does not, by itself, prove that goods
    were not delivered.
-   An overdue invoice is an accounts-payable exposure; the data alone
    does not establish why it remains unpaid or prove supplier
    misconduct.
-   Suppliers without purchasing history have insufficient evidence for
    a performance assessment. They should not automatically be
    classified as low risk.
-   AI-generated observations are decision support. Review them against
    source records and business context before taking operational
    action.

## 6. Run locally

### Repository files

The application expects these files in the project directory:

``` text
ProcurementDashboard/
├── app.py
├── dashboard_data.pkl
├── agent_outputs.json
├── crewai.png
├── requirements.txt
└── README.md
```

### Install dependencies

If the repository contains `requirements.txt`, install from it:

``` bash
python -m pip install -r requirements.txt
```

Otherwise, the core dashboard packages are:

``` bash
python -m pip install streamlit pandas numpy plotly
```

### Start Streamlit

``` bash
python -m streamlit run app.py
```

Open the local URL shown in the terminal (normally
`http://localhost:8501`).

## 7. Deploy with GitHub and Streamlit Community Cloud

1.  Create or open the GitHub repository for this project.
2.  Add `app.py`, `dashboard_data.pkl`, `agent_outputs.json`,
    `crewai.png`, `requirements.txt`, and this `README.md`.
3.  Commit and push the changes to GitHub.
4.  In Streamlit Community Cloud, create a new app and connect the
    repository, branch, and `app.py` entry point.
5.  Deploy and confirm that all required files load successfully.

Do not commit API keys, passwords, tokens, or other secrets. If the
deployed application only reads the exported data files, it does not
need the Gemini API key to display saved reports. The key is required
when running the CrewAI workflow that generates new reports.

## 8. Responsible interpretation

The Control Tower helps procurement and operations teams prioritize
investigation. It does not autonomously approve purchases, make supplier
decisions, release payments, or establish the cause of an exception.
Validate findings with purchase orders, receiving records, invoices,
payment records, and supplier communications before taking action.

------------------------------------------------------------------------

**Procurement Intelligence Control Tower \| Powered by CrewAI**
