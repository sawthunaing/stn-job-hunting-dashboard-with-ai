# Google Analytics 4 setup for the demo stack

This walks through getting GA4 wired into the public demo (port 3001).
Private app (port 3000) intentionally does not get analytics — it's a personal
tool, you don't need to track yourself.

## Part 1: Create GA4 property (10 min)

### 1. Sign in to Google Analytics

https://analytics.google.com

If you don't have an Analytics account yet, click **Start measuring** and:
- Account name: `Saw Personal Projects` (or whatever)
- Account data sharing: defaults are fine
- Click **Next**

### 2. Create a property

- Property name: `Job Hunting AI Demo`
- Reporting time zone: `(GMT+00:00) United Kingdom`
- Currency: GBP
- Click **Next**

### 3. Business details

- Industry category: `Computers & Electronics`
- Business size: `Small` (1-10 employees)
- How do you intend to use Google Analytics: tick whichever apply
- Click **Create**
- Accept the data processing terms

### 4. Set up data stream

You'll be taken to "Data streams". Choose **Web**:
- Website URL: `http://51.24.16.185:3001`
- Stream name: `Demo - Public`
- Enhanced measurement: leave defaults ON (auto-tracks page views, scrolls, outbound clicks)
- Click **Create stream**

### 5. Grab your Measurement ID

You'll now see a "Web stream details" page. Look at the top — there's a
**Measurement ID** in the format `G-XXXXXXXXXX` (one letter G, hyphen, 10
characters). Copy this.

That's the only thing you need from GA4.

## Part 2: Configure on EC2 (5 min)

### 1. SSH in

```bash
ssh ec2-user@51.24.16.185
cd ~/trajectory
```

### 2. Pull latest code

```bash
git pull
```

You should see the new files: `Analytics.tsx`, the updated `docker-compose.demo.yml`,
and the updated `Dockerfile.prod`.

### 3. Add the measurement ID to .env.demo

```bash
nano .env.demo
```

Find the line:
```
DEMO_GA_ID=
```

Add your measurement ID:
```
DEMO_GA_ID=G-XXXXXXXXXX
```

(Replace `G-XXXXXXXXXX` with your real ID from Part 1, Step 5.)

Save: Ctrl+X, Y, Enter.

### 4. Rebuild the demo frontend

The GA ID is baked in at build time, so rebuild is required.

```bash
sudo COMPOSE_DOCKER_CLI_BUILD=0 DOCKER_BUILDKIT=0 \
  docker compose -p trajectory-demo \
  -f docker-compose.demo.yml \
  --env-file .env.demo \
  up -d --build frontend
```

Takes ~5-10 min on t4g.small. Watch for `npm run build` completing successfully.

### 5. Verify

```bash
sudo docker exec trajectory-demo-frontend env | grep GA_ID
```

Should show `NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX`.

## Part 3: Test it (5 min)

### 1. Open the demo in incognito

`http://51.24.16.185:3001` in an incognito/private window (so no cached cookies).

### 2. You should see the consent banner

Bottom-right corner, dark card titled "A note on cookies" with **Allow analytics**
and **Decline** buttons.

### 3. Click "Allow analytics"

The banner disappears. GA4 scripts now load in the background.

### 4. Verify in GA4 Real-time view

In GA4: **Reports → Realtime**

You should see "1 user" within ~30 seconds. If you click around the demo, you'll
see the page paths in the "Top pages and screens" panel.

If nothing appears after 1-2 minutes:
- Open browser DevTools → Network tab → filter for "google"
- Reload the page
- You should see requests to `googletagmanager.com/gtag/js` and `google-analytics.com/g/collect`
- If those requests are missing, the GA ID didn't bake into the build correctly

### 5. Test the decline path

In a different incognito window:
- Click **Decline** on the banner
- Open Network tab → reload → there should be NO requests to google domains

This proves the consent gate works.

## Part 4: Day-2 — what you'll see

### The first day

- Your own visits will dominate the data. Filter yourself out by IP if you want
  (GA4 → Admin → Data Streams → tag → Configure tag settings → List unwanted
  referrals + Define internal traffic). Or just ignore early data.

### The first week

After your LinkedIn post:
- Spike of visitors on day 1 (post engagement)
- Drop-off on day 2-3 (LinkedIn algorithm decay)
- Steady trickle from people who saved/shared the post

### What to actually watch

In **Reports → Realtime** and **Reports → Engagement → Pages**:

- **Pages per session** — are visitors clicking around? <2 means they bounced.
- **Average engagement time** — under 30 sec means they didn't even read the
  funnel chart. Bad sign.
- **Traffic sources** — most should come from `lnkd.in` (LinkedIn). If you see
  unexpected sources (e.g. Hacker News), that's interesting feedback.
- **Top pages** — `/` should dominate. If `/applications` gets a lot of views,
  visitors are exploring deeper.

## Notes

### Privacy / GDPR

Even with the consent banner, you should also have a privacy policy. For
portfolio purposes, a one-page disclaimer is enough. The banner here is more
than most personal projects bother with — you're already ahead.

If you ever expand the audience to commercial use, you'd need:
- Proper privacy policy linking from the consent banner
- A "Manage cookie preferences" page
- Potentially Cookie Information's "Cookie Solution" or similar (£) for proper
  CMP compliance

For now (personal portfolio), the current setup is fine.

### Cost

GA4 Free tier covers:
- Up to 10M events/month
- 14 months of data retention
- All standard reports

You will not hit these limits on a portfolio demo.

### Disabling analytics later

If you want to remove GA4 (e.g. if you decide privacy matters more):

```bash
nano .env.demo
# Remove or empty the DEMO_GA_ID line
```

Then rebuild:
```bash
sudo COMPOSE_DOCKER_CLI_BUILD=0 DOCKER_BUILDKIT=0 \
  docker compose -p trajectory-demo \
  -f docker-compose.demo.yml \
  --env-file .env.demo \
  up -d --build frontend
```

The Analytics component returns `null` when no GA_ID is set — banner doesn't
show, no GA loaded, no cookies.
