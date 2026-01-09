// MCP Integration Templates
export interface MCPTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: "communication" | "productivity" | "development" | "data" | "travel" | "food";
  comingSoon?: boolean;
  config: {
    type: string;
    fields: {
      name: string;
      label: string;
      type: "text" | "password" | "url" | "textarea";
      placeholder?: string;
      required?: boolean;
      helper?: string;
    }[];
  };
  help?: {
    ctaLabel?: string;
    ctaUrl?: string;
    steps?: string[];
    note?: string;
  };
}

export const mcpTemplates: MCPTemplate[] = [
  {
    id: "gmail",
    name: "Gmail",
    description: "Read, search, and send emails through Gmail",
    icon: "Mail",
    category: "communication",
    config: {
      type: "gmail",
      fields: [],
    },
    help: {
      ctaLabel: "Google consent screen",
      ctaUrl: "https://myaccount.google.com/permissions",
      steps: [
        "Click Connect Gmail to launch Google OAuth with your signed-in account.",
        "Approve the Gmail Readonly scope (and email/profile) so we can fetch tokens.",
        "You'll be routed back here and the integration will show as connected.",
      ],
      note:
        "We store tokens per-user under your account. Revoke access anytime from your Google account permissions.",
    },
  },
  {
    id: "slack",
    name: "Slack",
    description: "Send messages and read channels in Slack",
    icon: "MessageSquare",
    category: "communication",
    comingSoon: true,
    config: {
      type: "slack",
      fields: [],
    },
    help: {
      ctaLabel: "Slack App Directory",
      ctaUrl: "https://api.slack.com/apps",
      steps: [
        "Click Connect Slack to launch Slack OAuth with your signed-in account.",
        "Approve the requested permissions (send messages, read channels).",
        "You'll be routed back here and the integration will show as connected.",
      ],
      note:
        "We store tokens per-user under your account. Revoke access anytime from your Slack workspace settings.",
    },
  },
  {
    id: "jira",
    name: "Jira",
    description: "Create, update, and search Jira issues",
    icon: "CheckSquare",
    category: "productivity",
    comingSoon: true,
    config: {
      type: "jira",
      fields: [],
    },
    help: {
      ctaLabel: "Atlassian Developer Console",
      ctaUrl: "https://developer.atlassian.com/console/myapps/",
      steps: [
        "Click Connect Jira to launch Atlassian OAuth with your signed-in account.",
        "Approve the requested Jira permissions so we can access your projects.",
        "You'll be routed back here and the integration will show as connected.",
      ],
      note:
        "We store tokens per-user under your account. Revoke access anytime from your Atlassian account settings.",
    },
  },
  {
    id: "github",
    name: "GitHub",
    description: "Access repositories, issues, and pull requests",
    icon: "Github",
    category: "development",
    config: {
      type: "github",
      fields: [],
    },
    help: {
      ctaLabel: "GitHub Developer Settings",
      ctaUrl: "https://github.com/settings/developers",
      steps: [
        "Click Connect GitHub to launch GitHub OAuth with your signed-in account.",
        "Approve the requested permissions (repo access, user profile).",
        "You'll be routed back here and the integration will show as connected.",
      ],
      note:
        "We store tokens per-user under your account. Revoke access anytime from your GitHub authorized applications.",
    },
  },
  {
    id: "uber",
    name: "Uber",
    description: "Get ride estimates and book Uber rides",
    icon: "Car",
    category: "travel",
    comingSoon: true,
    config: {
      type: "uber",
      fields: [],
    },
    help: {
      ctaLabel: "Uber Developer Portal",
      ctaUrl: "https://developer.uber.com/",
      steps: [
        "Click Connect Uber to launch Uber OAuth with your signed-in account.",
        "Approve the requested permissions (ride history, profile).",
        "You'll be routed back here and the integration will show as connected.",
      ],
      note:
        "We store tokens per-user under your account. Revoke access anytime from your Uber account settings.",
    },
  },
  {
    id: "confluence",
    name: "Confluence",
    description: "Search and read Confluence pages and spaces",
    icon: "BookOpen",
    category: "productivity",
    comingSoon: true,
    config: {
      type: "confluence",
      fields: [
        {
          name: "base_url",
          label: "Confluence URL",
          type: "url",
          placeholder: "https://your-domain.atlassian.net/wiki",
          helper: "Use the Confluence base URL for your site.",
          required: true,
        },
        {
          name: "user",
          label: "Email",
          type: "text",
          placeholder: "your-email@company.com",
          helper: "The email tied to your Atlassian account.",
          required: true,
        },
        {
          name: "api_token",
          label: "API Token",
          type: "password",
          placeholder: "Your Confluence API token",
          helper: "Reuse the Atlassian API token you generated for Jira/Confluence.",
          required: true,
        },
      ],
    },
    help: {
      ctaLabel: "Get Atlassian API Token",
      ctaUrl: "https://id.atlassian.com/manage-profile/security/api-tokens",
      steps: [
        "Create an API token once and reuse it for Confluence and Jira.",
        "Use the Confluence URL (https://your-domain.atlassian.net/wiki).",
      ],
    },
  },
  {
    id: "linear",
    name: "Linear",
    description: "Manage Linear issues and projects",
    icon: "Layers",
    category: "productivity",
    comingSoon: true,
    config: {
      type: "linear",
      fields: [
        {
          name: "api_key",
          label: "API Key",
          type: "password",
          placeholder: "lin_api_xxxxxxxxxxxx",
          helper: "Create in Linear - Settings - API - Personal API keys.",
          required: true,
        },
      ],
    },
    help: {
      ctaLabel: "Open Linear API Settings",
      ctaUrl: "https://linear.app/settings/api",
      steps: ["Create a Personal API key", "Copy and paste it here to connect Linear"],
    },
  },
  {
    id: "notion",
    name: "Notion",
    description: "Read and search Notion pages and databases",
    icon: "FileText",
    category: "productivity",
    comingSoon: true,
    config: {
      type: "notion",
      fields: [
        {
          name: "api_key",
          label: "Integration Token",
          type: "password",
          placeholder: "secret_xxxxxxxxxxxx",
          helper: "Create a Notion internal integration and share pages/databases with it.",
          required: true,
        },
      ],
    },
    help: {
      ctaLabel: "Create Notion Integration",
      ctaUrl: "https://www.notion.so/my-integrations",
      steps: [
        "Create an Internal Integration and copy the secret token (starts with secret_).",
        "Share the pages/databases you want the bot to access with that integration.",
      ],
    },
  },
  {
    id: "postgresql",
    name: "PostgreSQL",
    description: "Query your own PostgreSQL databases",
    icon: "Database",
    category: "data",
    comingSoon: true,
    config: {
      type: "postgresql",
      fields: [
        {
          name: "host",
          label: "Host",
          type: "text",
          placeholder: "localhost or db.example.com",
          helper: "Hostname or IP for your database.",
          required: true,
        },
        {
          name: "port",
          label: "Port",
          type: "text",
          placeholder: "5432",
          helper: "Defaults to 5432 if empty.",
          required: false,
        },
        {
          name: "user",
          label: "Username",
          type: "text",
          placeholder: "postgres",
          helper: "Database user with read/write access.",
          required: true,
        },
        {
          name: "password",
          label: "Password",
          type: "password",
          placeholder: "Database password",
          helper: "Will be stored encrypted; use a dedicated user if possible.",
          required: true,
        },
        {
          name: "db",
          label: "Database Name",
          type: "text",
          placeholder: "mydb",
          helper: "Which database to connect to on that host.",
          required: true,
        },
      ],
    },
    help: {
      steps: [
        "Use a network-reachable host/port and a least-privileged database user.",
        "We'll store these credentials securely; rotate them if you suspect compromise.",
      ],
      note: "Connection strings aren't supported yet-enter each field instead.",
    },
  },
  {
    id: "irctc",
    name: "IRCTC",
    description: "Search trains, check PNR status, and seat availability",
    icon: "Train",
    category: "travel",
    comingSoon: true,
    config: {
      type: "irctc",
      fields: [
        {
          name: "api_key",
          label: "RapidAPI Key",
          type: "password",
          placeholder: "Your RapidAPI key",
          helper: "Get your API key from RapidAPI IRCTC endpoint.",
          required: true,
        },
      ],
    },
    help: {
      ctaLabel: "Get RapidAPI Key",
      ctaUrl: "https://rapidapi.com/irctc-irctc-default/api/irctc1",
      steps: [
        "Sign up on RapidAPI and subscribe to the IRCTC API.",
        "Copy your RapidAPI key from the dashboard.",
        "Paste the key here to enable train search and PNR tracking.",
      ],
      note: "Free tier includes limited requests. Upgrade for more usage.",
    },
  },
];
