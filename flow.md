graph TD
    A[🕐 CRON Scheduler<br/>Déclenchement quotidien] --> B[📋 Planning Phase<br/>get_cities_to_scrape function]
    
    B --> C{🏙️ Villes à scraper ?}
    C -->|Oui| D[🔄 Pour chaque ville/type]
    C -->|Non| Z1[📨 Telegram: Aucune ville à scraper]
    
    D --> E[⏱️ Démarrage scraping<br/>Start timer + counters]
    E --> F[🕷️ Scraper Le Bon Coin<br/>Page 1]
    
    F --> G[📄 Récupérer annonces<br/>page courante]
    G --> H{🔍 URL existe déjà<br/>en base ?}
    
    H -->|Toutes nouvelles| I[💾 Insérer nouvelles annonces<br/>prospection_estates]
    H -->|Certaines existent| J[🔄 Insérer uniquement<br/>les nouvelles]
    H -->|Toutes existent| K[⏹️ Arrêter scraping<br/>cette ville/type]
    
    I --> L[👥 Lier aux utilisateurs<br/>user_prospections]
    J --> L
    
    L --> M{📄 Plus de pages ?}
    M -->|Oui| N[⏭️ Page suivante<br/>Rate limiting 2s]
    M -->|Non| K
    
    N --> O[📊 Increment counters<br/>pages_scraped++]
    O --> G
    
    K --> P[📊 Mettre à jour timestamp<br/>cities.last_scraped_*_at]
    P --> Q[📈 Log résultats ville<br/>success/error/warnings]
    
    Q --> R{🏙️ Autres villes ?}
    R -->|Oui| S[⏳ Rate limiting 5s<br/>entre villes]
    S --> D
    R -->|Non| T[🏁 Agrégation finale<br/>Total stats]
    
    T --> U[📨 Telegram Notification<br/>Rapport final complet]
    U --> Z2[✅ Fin du job]
    
    %% Error handling
    F -.->|403/Error| V[❌ Log erreur ville]
    G -.->|Error| V
    V --> W[🔄 Retry ou Skip]
    W --> Q
    
    %% Notification details
    subgraph "📨 Telegram Notification Content"
        N1[🏆 Villes scrapées avec succès]
        N2[❌ Erreurs par ville]  
        N3[⚠️ Warnings villes 0 annonces]
        N4[⏱️ Temps total exécution]
        N5[📊 Stats: nouvelles/doublons/total]
        N6[🗓️ Timestamp fin de job]
    end
    
    %% In-memory counters
    subgraph "🔢 Compteurs en mémoire"
        C1[cities_success = 0]
        C2[cities_errors = 0] 
        C3[cities_warnings = 0]
        C4[total_new_listings = 0]
        C5[total_duplicates = 0]
        C6[start_time]
    end
    
    %% Database interactions
    subgraph "🗄️ Database Operations"
        DB1[cities table<br/>get + update timestamps]
        DB2[prospection_estates<br/>insert new listings]
        DB3[user_prospections<br/>link to users]
        DB4[user_cities<br/>get preferences]
    end
    
    %% Connections to data
    B -.-> DB4
    B -.-> DB1
    I -.-> DB2
    L -.-> DB3
    P -.-> DB1
    
    %% Counter updates
    E -.-> C6
    L -.-> C4
    J -.-> C5
    Q -.-> C1
    V -.-> C2
    K -.-> C3
    
    %% Notification data
    U -.-> N1
    U -.-> N2
    U -.-> N3
    U -.-> N4
    U -.-> N5
    U -.-> N6
    
    Z1 --> Z2
    
    %% Styles
    classDef processBox fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef decisionBox fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef dataBox fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef telegramBox fill:#0088cc,stroke:#white,stroke-width:2px,color:#white
    classDef errorBox fill:#ffebee,stroke:#c62828,stroke-width:2px
    
    class A,E,F,G,I,J,L,N,O,P,Q,S,T processBox
    class C,H,M,R decisionBox
    class DB1,DB2,DB3,DB4,C1,C2,C3,C4,C5,C6 dataBox
    class U,Z1,N1,N2,N3,N4,N5,N6 telegramBox
    class V,W errorBox