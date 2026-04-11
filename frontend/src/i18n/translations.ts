/**
 * Wakili Internationalization
 * All UI strings in English (en) and Swahili (sw)
 */
export type Lang = "en" | "sw";

export const translations = {
  en: {
    // Navigation
    nav_dashboard:  "Dashboard",
    nav_documents:  "Documents",
    nav_chat:       "Ask Wakili",
    nav_analytics:  "Analytics",
    nav_logout:     "Sign Out",

    // Auth
    login_title:    "Welcome back",
    login_subtitle: "Sign in to Wakili",
    register_title: "Create account",
    email:          "Email address",
    password:       "Password",
    full_name:      "Full name",
    sign_in:        "Sign in",
    sign_up:        "Create account",
    no_account:     "Don't have an account?",
    have_account:   "Already have an account?",

    // Dashboard
    dash_welcome:    "Welcome to Wakili",
    dash_subtitle:   "RAG-powered legal document analysis",
    dash_upload:     "Upload Document",
    dash_recent:     "Recent Documents",
    dash_no_docs:    "No documents yet. Upload your first legal document.",

    // Upload
    upload_title:    "Upload Legal Document",
    upload_drag:     "Drag and drop your document here",
    upload_or:       "or",
    upload_browse:   "Browse files",
    upload_formats:  "Supports PDF, DOCX, TXT up to 20MB",
    upload_btn:      "Upload & Analyze",

    // Document viewer
    doc_clauses:     "Clauses",
    doc_risks:       "Risk Flags",
    doc_obligations: "Obligations",
    doc_processing:  "Processing document...",
    risk_high:       "High Risk",
    risk_medium:     "Medium Risk",
    risk_low:        "Low Risk",

    // Chat
    chat_placeholder: "Ask a legal question about your documents...",
    chat_send:        "Send",
    chat_thinking:    "Wakili is analyzing...",
    chat_no_docs:     "Please upload a document before asking questions.",

    // Analytics
    analytics_title:   "Analytics",
    total_documents:   "Total Documents",
    total_queries:     "Questions Asked",
    avg_response:      "Avg Response Time",
    languages_used:    "Languages Used",

    // Status
    status_ready:      "Ready",
    status_processing: "Processing",
    status_error:      "Error",
  },

  sw: {
    // Navigation
    nav_dashboard:  "Dashibodi",
    nav_documents:  "Hati",
    nav_chat:       "Uliza Wakili",
    nav_analytics:  "Takwimu",
    nav_logout:     "Toka",

    // Auth
    login_title:    "Karibu tena",
    login_subtitle: "Ingia kwenye Wakili",
    register_title: "Fungua akaunti",
    email:          "Barua pepe",
    password:       "Nenosiri",
    full_name:      "Jina kamili",
    sign_in:        "Ingia",
    sign_up:        "Fungua akaunti",
    no_account:     "Huna akaunti?",
    have_account:   "Una akaunti tayari?",

    // Dashboard
    dash_welcome:    "Karibu Wakili",
    dash_subtitle:   "Uchambuzi wa hati za kisheria kwa RAG System",
    dash_upload:     "Pakia Hati",
    dash_recent:     "Hati za Hivi Karibuni",
    dash_no_docs:    "Hakuna hati bado. Pakia hati yako ya kwanza ya kisheria.",

    // Upload
    upload_title:    "Pakia Hati ya Kisheria",
    upload_drag:     "Buruta na uache hati yako hapa",
    upload_or:       "au",
    upload_browse:   "Vinjari faili",
    upload_formats:  "Inasaidia PDF, DOCX, TXT hadi 20MB",
    upload_btn:      "Pakia na Changanua",

    // Document viewer
    doc_clauses:     "Vifungu",
    doc_risks:       "Alama za Hatari",
    doc_obligations: "Wajibu",
    doc_processing:  "Inachakata hati...",
    risk_high:       "Hatari Kubwa",
    risk_medium:     "Hatari ya Kati",
    risk_low:        "Hatari Ndogo",

    // Chat
    chat_placeholder: "Uliza swali la kisheria kuhusu hati zako...",
    chat_send:        "Tuma",
    chat_thinking:    "Wakili anachambua...",
    chat_no_docs:     "Tafadhali pakia hati kabla ya kuuliza maswali.",

    // Analytics
    analytics_title:   "Takwimu",
    total_documents:   "Jumla ya Hati",
    total_queries:     "Maswali Yaliyoulizwa",
    avg_response:      "Muda wa Wastani wa Kujibu",
    languages_used:    "Lugha Zilizotumika",

    // Status
    status_ready:      "Tayari",
    status_processing: "Inachakata",
    status_error:      "Hitilafu",
  },
} as const;

export type TranslationKey = keyof typeof translations.en;
