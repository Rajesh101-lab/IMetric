# Meta App Review Submission Guide for Page Metrics

To get your Meta App approved for **Production Mode** (allowing your agency app to query any public Instagram Business or Creator account via Business Discovery without Error #10), you need to submit your app for **App Review**.

Here are all the exact details, descriptions, and steps you need to provide to Meta.

---

## 1. Required Permissions to Submit for Review
In your Meta App Dashboard under **App Review** > **Permissions and Features**, request review for:
1. **`instagram_basic`**
2. **`pages_show_list`**
3. **`business_management`**
*(Note: `instagram_graph_user_media` is deprecated/not needed for Business Discovery; these 3 permissions are the exact standard set required).*

---

## 2. App Details & Compliance URLs (Using GitHub)
You can publish your repository to GitHub and use your GitHub raw or markdown file URLs for Meta:
- **Privacy Policy URL**: `https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/SOCIAL-MEDIA-HUNT/main/privacy-policy.md`
- **Terms of Service URL**: `https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/SOCIAL-MEDIA-HUNT/main/terms-of-service.md`
*(Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username).*

---

## 3. Step-by-Step Testing Instructions for Meta Reviewers

Copy and paste this exact instruction block into the **"Instructions for Reviewers"** field on Meta:

> ### Test Instructions
> 1. Log in to the Page Metrics agency dashboard using the test credentials provided below:
>    - **Agency ID**: `agency_admin`
>    - **Password**: `SecureAgency123!`
> 2. Once logged into the dashboard, navigate to the **Add Page** tab (tap the `+` button in the bottom dock).
> 3. Enter any public Instagram Business or Creator handle (e.g., `@nike` or `@starbucks`) in the input box and tap **Add Page**.
> 4. The application uses the Instagram Graph API (Business Discovery) to instantly retrieve follower count, reel view counts, like counts, and engagement ratios for the specified page.
> 5. The metrics appear immediately on the agency analytics dashboard.

---

## 4. Explanation of Use Case (Why You Need Access)

Copy and paste this professional description into the **"Use Case Description"** field on Meta:

> **Use Case Description**:
> Page Metrics is an internal analytics workspace designed for social media management agencies. Agencies manage multiple client Instagram Business and Creator accounts and need to track performance metrics across competitor and client pages (such as audience size, reel views, median reach, and engagement ratios).
>
> The app utilizes the Instagram Graph API's **Business Discovery** feature to query public Business/Creator profile metrics on behalf of authorized agency administrators, enabling them to generate campaign reports and track social media growth efficiently in one unified dashboard.

---

## 5. Screencast Recording Checklist (Required by Meta)
Meta requires a short screen recording (MP4, max 100MB) showing how the reviewer can test your app.
Make sure your video shows:
1. Logging into the app with the test credentials.
2. Navigating to the **Add Page** screen.
3. Typing an Instagram handle (e.g. `@nike`) and clicking **Add Page**.
4. The dashboard loading and displaying the live metrics.
