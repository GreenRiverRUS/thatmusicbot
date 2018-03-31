## thatmusicbot
Inline telegram bot for searching and sending music.
Requires [thatmusic api](https://github.com/GreenRiverRUS/thatmusic-api) to work.

### How to start bot
- Clone repo
- Create your own `.env` by coping `.env.default`
- Place your telegram bot token into `.env`
- Set api endpoint which points to your instance of [thatmusic api](https://github.com/GreenRiverRUS/thatmusic-api)
- Specify your host name in `.env` _(your machine should have a public signed ssl host)_.
Or use self-signed certificate and place path to its public part into `.env`
_(you should have [nginx](https://docs.nginx.com/nginx/admin-guide/security-controls/terminating-ssl-tcp/) or smth similar for ssl termination)_
- Start: `docker-compose -p thatmusic up --build -d`
