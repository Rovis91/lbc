# LeBonCoin Real Estate Scraper Orchestrator

A production-ready Python orchestrator that automatically scrapes real estate listings from LeBonCoin and stores them in a Supabase database. This system follows a specific workflow to efficiently collect, deduplicate, and distribute property listings to interested users.

## 🏗️ Architecture

This orchestrator is built on top of the excellent [lbc](https://github.com/etienne-hd/lbc) Python client for LeBonCoin's API, created by [Etienne HODE](https://github.com/etienne-hd). The original scraper provides the core functionality for interacting with LeBonCoin's search API.

### Components

- **`main.py`** - Main orchestrator script (cron entry point)
- **`db.py`** - Supabase database operations
- **`scraper.py`** - LeBonCoin scraping logic wrapper
- **`telegram.py`** - Telegram notification system

## 🔄 Workflow

The orchestrator follows this automated workflow:

1. **Planning Phase**: Query database for cities that need scraping based on user preferences and last scrape timestamps
2. **Scraping Phase**: For each city/listing type combination:
   - Scrape listings from LeBonCoin
   - Deduplicate by URL
   - Store new listings in database
   - Link listings to interested users
3. **Notification Phase**: Send comprehensive report via Telegram

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Supabase database with the provided schema
- Telegram bot token and user ID
- Ubuntu VPS (recommended for production)

### Installation

1. **Clone and install dependencies**:
   ```bash
   git clone <your-repo-url>
   cd lbc
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   # Create .env file
   cat > .env << EOF
   VITE_SUPABASE_URL=your_supabase_url
   VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_USER_ID=your_telegram_user_id
   EOF
   ```

3. **Run the orchestrator**:
   ```bash
   python main.py
   ```

### Production Deployment

For production use on a VPS:

1. **Set up cron job** (runs daily at 2 AM):
   ```bash
   # Edit crontab
   crontab -e
   
   # Add this line
   0 2 * * * cd /path/to/lbc && python main.py >> /var/log/lbc-scraper.log 2>&1
   ```

2. **Create log directory**:
   ```bash
   sudo mkdir -p /var/log
   sudo touch /var/log/lbc-scraper.log
   sudo chown $USER:$USER /var/log/lbc-scraper.log
   ```

## 📊 Database Schema

The orchestrator requires a Supabase database with the following key tables:

- `cities` - City information with coordinates and scrape timestamps
- `users` - User accounts and preferences
- `user_cities` - User preferences for specific cities
- `prospection_estates` - Property listings (unique by URL)
- `user_prospections` - Links between users and listings

The database includes a `get_cities_to_scrape()` function that determines which cities need scraping based on:
- User preferences (`user_cities` table)
- Last scrape timestamps
- Configurable scrape interval

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_SUPABASE_URL` | Supabase project URL | Yes |
| `VITE_SUPABASE_ANON_KEY` | Supabase anonymous key | Yes |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Yes |
| `TELEGRAM_USER_ID` | Telegram user ID for notifications | Yes |

### Scraping Parameters

The orchestrator uses these default parameters:
- **Max listings per city**: 100
- **Rate limiting**: 2 seconds between pages, 5 seconds between cities
- **Scrape interval**: 24 hours (configurable in database function)

## 📨 Notifications

The system sends Telegram notifications in this format:

```
🏆 SCRAPING COMPLETED
─────────────────────
✅ Successful cities: 5/7
❌ Errors: 2 cities
⚠️ Warnings: 3 cities (0 listings)
⏱️ Duration: 12min 34s
📊 New listings: 156
🔄 Duplicates avoided: 43  
🗓️ Finished: 2025-01-15 14:23:45
```

## 🛠️ Development

### Testing Locally

1. **Set up test data** in your Supabase database:
   ```sql
   -- Add test cities
   INSERT INTO cities (name, zipcode, latitude, longitude, department_name) 
   VALUES ('Paris', '75001', 48.86, 2.34, 'Paris');
   
   -- Add test users and preferences
   INSERT INTO users (id, email) VALUES ('test-user-id', 'test@example.com');
   INSERT INTO user_cities (user_id, city_id, scrape_sale, scrape_rent) 
   VALUES ('test-user-id', 1, true, true);
   ```

2. **Run with test data**:
   ```bash
   python main.py
   ```

### Monitoring

- **Logs**: Check `/var/log/lbc-scraper.log` for detailed execution logs
- **Telegram**: Receive real-time notifications about scraping status
- **Database**: Monitor `prospection_estates` table for new listings

## 🔒 Security & Best Practices

- **Rate Limiting**: Built-in delays prevent overwhelming LeBonCoin's servers
- **Error Handling**: Comprehensive error handling with graceful degradation
- **Deduplication**: Prevents duplicate listings using URL uniqueness
- **Environment Variables**: Secure credential management
- **Logging**: Detailed logging for debugging and monitoring

## 📝 License

This project is built on top of the [lbc](https://github.com/etienne-hd/lbc) library by Etienne HODE, which is licensed under MIT.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues related to:
- **LeBonCoin API**: Check the [original lbc repository](https://github.com/etienne-hd/lbc)
- **This orchestrator**: Open an issue in this repository
- **Database schema**: Refer to the provided SQL schema file

---

**Note**: This orchestrator is designed for production use and follows the flowchart logic specified in `flow.md`. It's optimized for minimal resource usage and maximum reliability.