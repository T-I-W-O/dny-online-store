# DNY SmartRetail Platform 🛒

DNY is a full-featured e-commerce platform built with **Django**, designed for both customer shopping experiences and powerful administrative control. It combines an interactive storefront with real-time business insights for managing products, customers, and sales.

---

## 🌟 Advanced Features

### 🛍️ Customer Experience
* **Interactive UI:** Responsive and dynamic landing page for product discovery.
* **Authentication System:** User registration, login, and profile management.
* **Smart Cart & Checkout:** Add to cart, manage items, and complete orders.
* **Order Tracking:** Automatic Transaction ID generation for tracking and pickup.

### 🧠 Administrative Dashboard
* **Sales Intelligence:** Track most sold products and top customers.
* **Inventory Control:** Full product management (Add, Edit, Delete).
* **Customer Supervision:** View users and their purchase activity.
* **Admin Notices:** Push announcements or updates to users.

---

## 📸 Visual Overview

### 🎥 Full System Demo
*(Complete walkthrough of the platform)*

### Customer view

![LandingPage](images/landingpage.png)
![Home](images/homepage.png)
![Product](images/product_description.png)
![Cart](images/cart.png)


### 🔐 Authentication & User
![Login](images/login.png)
![Register](images/register.png)
![Profile](images/profile.png)

### 🧠 Admin Dashboard
![Dashboard](images/dashboard.png)

* watch **Demo.mp4** and other admin functionality in the images files.

---

## 🛠️ Tech Stack

* **Backend:** Django (Python)
* **Frontend:** HTML5, CSS3, JavaScript
* **Database:** SQLite / PostgreSQL
* **Media Storage:** Cloudinary
* **Payments:** Paystack (Test Mode)

---

## ⚙️ Setup & Installation

1. **Clone the repository:**
```bash
git clone https://github.com/T-I-W-O/dny-online-store.git
cd dny-online-store
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Create a `.env` file and add the following:**
```env
PAYSTACK_SECRET_KEY=
PAYSTACK_PUBLIC_KEY=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
SECRET_KEY=

CLOUD_NAME=
API_KEY=
API_SECRET=

DEBUG=
ALLOWED_HOSTS=
DATABASE_URL=

DJANGO_SU_USERNAME=
DJANGO_SU_EMAIL=
DJANGO_SU_PASSWORD=
```

4. **Run migrations:**
```bash
python manage.py migrate
```

5. **Run the server:**
```bash
python manage.py runserver
```

6. Open your browser at `http://127.0.0.1:8000/`

---

## 🔐 Notes

* Admin route has been customized from `/admin` to `/secret` for added security.
* Cloudinary is used for media storage (already included in requirements).
* Paystack integration is in **Test Mode** (no real transactions).

---

## 📌 Status

- Complete e-commerce system with admin and customer flows
- Payment, analytics, and authentication fully implemented

---

## 🚀 Future Improvements

- Real payment deployment
- Email automation improvements
- Advanced filtering and search
- UI/UX enhancements

