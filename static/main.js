// RendezVousDZ — Main JavaScript
// Unified dark mode + language switcher + real-time queue

// ═══════════════════════════════════════════════════════
// 🌙 DARK MODE
// ═══════════════════════════════════════════════════════
const THEME_KEY = 'rvdz_theme';

function _applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);

    // Update toggle button icons
    document.querySelectorAll('.theme-toggle').forEach(btn => {
        const li = btn.querySelector('.theme-icon-light');
        const di = btn.querySelector('.theme-icon-dark');
        if (li) li.style.display = theme === 'dark' ? 'none' : '';
        if (di) di.style.display  = theme === 'dark' ? ''     : 'none';
    });

    // Swap logos
    document.querySelectorAll('img.auth-logo, img.dashboard-logo').forEach(img => {
        img.src = theme === 'dark' ? '/static/logo_white.png' : '/static/logo_blue.png';
    });

    // Rebuild analytics charts if present
    if (window._chartsBuilt && typeof buildCharts === 'function') {
        setTimeout(buildCharts, 50);
    }
}

function toggleTheme() {
    const cur = document.documentElement.getAttribute('data-theme') || 'light';
    _applyTheme(cur === 'dark' ? 'light' : 'dark');
}

window.toggleTheme = toggleTheme;

// Apply theme immediately (before DOMContentLoaded) to prevent flash
(function() {
    const saved = localStorage.getItem(THEME_KEY) || 'light';
    document.documentElement.setAttribute('data-theme', saved);
})();


// ═══════════════════════════════════════════════════════
// 🌐 LANGUAGE SYSTEM
// ═══════════════════════════════════════════════════════
const LANG_KEY       = 'rvdz_lang';
const SUPPORTED_LANGS = ['en', 'fr', 'ar'];

const TRANSLATIONS = {
    en: {
        // Nav
        logout: 'Logout',
        settings: '⚙️ Settings',
        analytics: '📊 Analytics',
        publicLink: '📋 Public Booking Link',
        liveQueue: '⚡ Live Queue',
        backToDashboard: '← Back to Dashboard',
        backToHome: '← Back to Home',
        backToLogin: '← Back to Login',
        dashboard: 'Dashboard',

        // Dashboard
        currentQueue: 'Current Queue',
        dailyLimit: 'Daily Limit',
        remainingSlots: 'Remaining Slots',
        avgServiceTime: '⏱️ Avg Service Time',
        basedOnData: 'Based on recent data',
        addClientTitle: 'Add Client to Queue',
        clientNamePlaceholder: 'Client Name',
        phonePlaceholder: 'Phone (Optional)',
        addToQueue: 'Add to Queue',
        queueFull: 'Queue Full',
        todaysQueue: "Today's Queue",
        markDone: 'Mark Done',
        skip: 'Skip',
        noClients: 'No clients in queue',
        addClientHint: 'Add a client above to get started',
        queueFullAlert: '⚠️ Queue Full - Daily limit reached',
        min: 'min',

        // Public booking
        joinQueue: 'Join Queue',
        yourName: 'Your Name',
        phoneNumber: 'Phone Number',
        fullName: 'Full Name',
        yourPosition: 'Your position',
        estWaitTime: '⏱️ Estimated Wait Time',
        youreInQueue: "You're in the Queue!",
        youreNext: "🎉 You're next!",
        servedShortly: "You'll be served shortly",
        pleaseWait: 'Please wait for your turn.',
        canClose: 'You can close this page now.',
        poweredBy: 'Powered by',
        currentQueueStatus: 'Current Queue',
        businessNotFound: 'Business Not Found',
        businessNotFoundSub: "The business you're looking for doesn't exist.",
        queueFullTitle: '⚠️ Queue Full',
        queueFullSub: "Sorry, we've reached our daily limit.",
        tryTomorrow: 'Please try again tomorrow.',

        // Settings
        businessSettings: 'Business Settings',
        businessSettingsSub: 'Update your business information',
        businessInfo: '🏢 Business Info',
        businessName: 'Business Name',
        category: 'Category',
        city: 'City',
        maxClients: 'Max Clients Per Day',
        maxClientsSub: 'Changes apply to future bookings only',
        saveSettings: '💾 Save Settings',
        settingsSaved: '✅ Settings saved successfully!',
        digitalDisplay: '📺 Digital Display Mode',
        digitalDisplaySub: 'Put this on a tablet or TV for your waiting clients',
        openDisplay: '🖥️ Open Display Screen',

        // Auth — Login
        welcomeBack: 'Welcome Back',
        welcomeBackSub: 'Sign in to manage your queue',
        signIn: 'Sign In',
        emailAddress: 'Email Address',
        password: 'Password',
        forgotPassword: 'Forgot your password?',
        noAccount: "Don't have an account?",
        createOne: 'Create one now',
        orDivider: 'or',

        // Auth — Register
        createAccount: 'Create Account',
        createAccountSub: 'Start managing your queue today',
        minChars: 'Minimum 8 characters',
        haveAccount: 'Already have an account?',
        signInHere: 'Sign in here',
        registerSuccess: '✅ Account created! Please check your email to verify your account before logging in.',

        // Auth — Forgot password
        resetPassword: 'Reset Password',
        resetPasswordSub: 'Enter your email to receive a reset link',
        sendResetLink: 'Send Reset Link',
        forgotSuccess: '✅ If an account exists with that email, a reset link has been sent. Please check your inbox.',

        // Auth — Reset password
        newPassword: 'New Password',
        newPasswordSub: 'Choose a strong password',
        newPasswordLabel: 'New Password',
        newPasswordPlaceholder: 'At least 8 characters',
        confirmPassword: 'Confirm Password',
        confirmPasswordPlaceholder: 'Repeat your password',
        updatePassword: 'Update Password',
        resetSuccess: '✅ Your password has been updated. You can now log in.',
        goToLogin: '→ Go to Login',
        requestNewLink: 'Request a new reset link',

        // Create business
        createBusiness: 'Create Your Business',
        createBusinessSub: 'Set up your queue management system',
        createBusinessBtn: 'Create Business',
        businessNamePlaceholder: 'e.g., Elite Barber Shop',
        cityPlaceholder: 'e.g., Algiers',
        selectCategory: 'Select a category',

        // Analytics
        analyticsTitle: '📊 Analytics',
        totalClients: 'Total Clients',
        thisWeek: 'This Week',
        avgServiceTimeLabel: 'Avg Service Time',
        completionRate: 'Completion Rate',
        skipRate: 'Skip Rate',
        busiestDay: 'Busiest Day (30d)',
        dailyClientsChart: '📆 Daily Clients — Last 7 Days',
        peakHoursChart: '🕐 Peak Hours',
        last30days: 'Last 30 days',
        weeklyChart: '📈 Weekly Performance — Last 4 Weeks',
        allTimeStatus: '🍩 All-Time Status',
        allTimeStatusSub: 'Breakdown of all entries',
        noDataYet: 'No data yet — start adding clients to see trends.',
        noHourlyData: 'No hourly data yet.',
        noWeeklyData: 'No weekly data yet.',
        legendTotal: 'Total',
        legendDone: 'Done',
        legendSkipped: 'Skipped',
        legendCompleted: 'Completed',
        analyticsRefresh: 'RendezVousDZ © 2026 · Analytics refreshed on page load',

        // Category options
        barber: 'Barber Shop', salon: 'Hair Salon', clinic: 'Medical Clinic',
        dentist: 'Dentist', spa: 'Spa & Wellness', restaurant: 'Restaurant', other: 'Other',

        // Days
        monday: 'Monday', tuesday: 'Tuesday', wednesday: 'Wednesday',
        thursday: 'Thursday', friday: 'Friday', saturday: 'Saturday', sunday: 'Sunday',

        // Home
        welcomeTitle: 'Welcome to RendezVousDZ',
        welcomeSub: 'Professional Digital Queue Management System',
        getStarted: 'Get Started',
        featFastTitle: 'Fast & Efficient',
        featFastDesc: 'Streamline your customer flow with real-time queue management',
        featEasyTitle: 'Easy to Use',
        featEasyDesc: 'Intuitive interface designed for seamless user experience',
        featSecureTitle: 'Secure & Reliable',
        featSecureDesc: 'Your data is protected with enterprise-grade security',

        // Footer
        footer: 'RendezVousDZ © 2026 - Professional Queue Management System',
    },

    fr: {
        logout: 'Déconnexion',
        settings: '⚙️ Paramètres',
        analytics: '📊 Analytique',
        publicLink: '📋 Lien de réservation',
        liveQueue: '⚡ File en direct',
        backToDashboard: '← Tableau de bord',
        backToHome: '← Accueil',
        backToLogin: '← Retour à la connexion',
        dashboard: 'Tableau de bord',

        currentQueue: 'File actuelle',
        dailyLimit: 'Limite journalière',
        remainingSlots: 'Places restantes',
        avgServiceTime: '⏱️ Temps moy. service',
        basedOnData: 'Basé sur données récentes',
        addClientTitle: 'Ajouter un client',
        clientNamePlaceholder: 'Nom du client',
        phonePlaceholder: 'Téléphone (facultatif)',
        addToQueue: 'Ajouter à la file',
        queueFull: 'File complète',
        todaysQueue: "File d'aujourd'hui",
        markDone: 'Terminé',
        skip: 'Passer',
        noClients: 'Aucun client en file',
        addClientHint: 'Ajoutez un client ci-dessus',
        queueFullAlert: '⚠️ File complète - Limite atteinte',
        min: 'min',

        joinQueue: 'Rejoindre la file',
        yourName: 'Votre nom',
        phoneNumber: 'Numéro de téléphone',
        fullName: 'Nom complet',
        yourPosition: 'Votre position',
        estWaitTime: "⏱️ Temps d'attente estimé",
        youreInQueue: 'Vous êtes dans la file !',
        youreNext: "🎉 C'est votre tour !",
        servedShortly: 'Vous serez servi bientôt',
        pleaseWait: 'Veuillez attendre votre tour.',
        canClose: 'Vous pouvez fermer cette page.',
        poweredBy: 'Propulsé par',
        currentQueueStatus: 'File actuelle',
        businessNotFound: 'Entreprise introuvable',
        businessNotFoundSub: "L'entreprise que vous cherchez n'existe pas.",
        queueFullTitle: '⚠️ File complète',
        queueFullSub: 'Désolé, nous avons atteint la limite journalière.',
        tryTomorrow: 'Veuillez réessayer demain.',

        businessSettings: 'Paramètres',
        businessSettingsSub: 'Mettez à jour vos informations',
        businessInfo: '🏢 Infos entreprise',
        businessName: "Nom de l'entreprise",
        category: 'Catégorie',
        city: 'Ville',
        maxClients: 'Max clients par jour',
        maxClientsSub: 'Applicable aux futures réservations uniquement',
        saveSettings: '💾 Enregistrer',
        settingsSaved: '✅ Paramètres enregistrés !',
        digitalDisplay: '📺 Affichage numérique',
        digitalDisplaySub: 'Mettez ceci sur une tablette ou TV pour vos clients',
        openDisplay: "🖥️ Ouvrir l'affichage",

        welcomeBack: 'Bon retour',
        welcomeBackSub: 'Connectez-vous pour gérer votre file',
        signIn: 'Se connecter',
        emailAddress: 'Adresse e-mail',
        password: 'Mot de passe',
        forgotPassword: 'Mot de passe oublié ?',
        noAccount: 'Pas de compte ?',
        createOne: 'En créer un',
        orDivider: 'ou',

        createAccount: 'Créer un compte',
        createAccountSub: "Commencez à gérer votre file aujourd'hui",
        minChars: 'Minimum 8 caractères',
        haveAccount: 'Déjà un compte ?',
        signInHere: 'Se connecter',
        registerSuccess: '✅ Compte créé ! Vérifiez votre e-mail avant de vous connecter.',

        resetPassword: 'Réinitialiser',
        resetPasswordSub: 'Entrez votre e-mail pour recevoir un lien',
        sendResetLink: 'Envoyer le lien',
        forgotSuccess: '✅ Si un compte existe avec cet e-mail, un lien a été envoyé.',

        newPassword: 'Nouveau mot de passe',
        newPasswordSub: 'Choisissez un mot de passe fort',
        newPasswordLabel: 'Nouveau mot de passe',
        newPasswordPlaceholder: 'Au moins 8 caractères',
        confirmPassword: 'Confirmer',
        confirmPasswordPlaceholder: 'Répétez votre mot de passe',
        updatePassword: 'Mettre à jour',
        resetSuccess: '✅ Mot de passe mis à jour. Vous pouvez vous connecter.',
        goToLogin: '→ Aller à la connexion',
        requestNewLink: 'Demander un nouveau lien',

        createBusiness: 'Créer votre entreprise',
        createBusinessSub: 'Configurez votre système de file',
        createBusinessBtn: 'Créer l\'entreprise',
        businessNamePlaceholder: 'ex. Salon Elite',
        cityPlaceholder: 'ex. Alger',
        selectCategory: 'Sélectionner une catégorie',

        analyticsTitle: '📊 Analytique',
        totalClients: 'Total clients',
        thisWeek: 'Cette semaine',
        avgServiceTimeLabel: 'Temps moy. service',
        completionRate: 'Taux de complétion',
        skipRate: 'Taux de passage',
        busiestDay: 'Jour le plus chargé (30j)',
        dailyClientsChart: '📆 Clients quotidiens — 7 derniers jours',
        peakHoursChart: '🕐 Heures de pointe',
        last30days: '30 derniers jours',
        weeklyChart: '📈 Performance hebdomadaire — 4 dernières semaines',
        allTimeStatus: '🍩 Statut global',
        allTimeStatusSub: 'Répartition de toutes les entrées',
        noDataYet: 'Pas encore de données — ajoutez des clients.',
        noHourlyData: 'Pas encore de données horaires.',
        noWeeklyData: 'Pas encore de données hebdomadaires.',
        legendTotal: 'Total',
        legendDone: 'Terminés',
        legendSkipped: 'Passés',
        legendCompleted: 'Complétés',
        analyticsRefresh: 'RendezVousDZ © 2026 · Données actualisées au chargement',

        barber: 'Barbier', salon: 'Salon de coiffure', clinic: 'Clinique médicale',
        dentist: 'Dentiste', spa: 'Spa & Bien-être', restaurant: 'Restaurant', other: 'Autre',

        monday: 'Lundi', tuesday: 'Mardi', wednesday: 'Mercredi',
        thursday: 'Jeudi', friday: 'Vendredi', saturday: 'Samedi', sunday: 'Dimanche',

        welcomeTitle: 'Bienvenue sur RendezVousDZ',
        welcomeSub: 'Système de gestion de file professionnel',
        getStarted: 'Commencer',
        featFastTitle: 'Rapide & Efficace',
        featFastDesc: 'Optimisez le flux de vos clients en temps réel',
        featEasyTitle: 'Facile à utiliser',
        featEasyDesc: "Interface intuitive pour une expérience fluide",
        featSecureTitle: 'Sécurisé & Fiable',
        featSecureDesc: 'Vos données sont protégées avec une sécurité de niveau entreprise',

        footer: 'RendezVousDZ © 2026 - Système professionnel de gestion de file',
    },

    ar: {
        logout: 'تسجيل الخروج',
        settings: '⚙️ الإعدادات',
        analytics: '📊 التحليلات',
        publicLink: '📋 رابط الحجز العام',
        liveQueue: '⚡ الطابور المباشر',
        backToDashboard: '→ لوحة التحكم',
        backToHome: '→ الرئيسية',
        backToLogin: '→ العودة لتسجيل الدخول',
        dashboard: 'لوحة التحكم',

        currentQueue: 'الطابور الحالي',
        dailyLimit: 'الحد اليومي',
        remainingSlots: 'الأماكن المتبقية',
        avgServiceTime: '⏱️ متوسط وقت الخدمة',
        basedOnData: 'بناءً على البيانات الأخيرة',
        addClientTitle: 'إضافة عميل إلى الطابور',
        clientNamePlaceholder: 'اسم العميل',
        phonePlaceholder: 'الهاتف (اختياري)',
        addToQueue: 'إضافة إلى الطابور',
        queueFull: 'الطابور ممتلئ',
        todaysQueue: 'طابور اليوم',
        markDone: 'تم',
        skip: 'تخطي',
        noClients: 'لا يوجد عملاء في الطابور',
        addClientHint: 'أضف عميلاً للبدء',
        queueFullAlert: '⚠️ الطابور ممتلئ - تم الوصول للحد اليومي',
        min: 'دقيقة',

        joinQueue: 'الانضمام للطابور',
        yourName: 'اسمك',
        phoneNumber: 'رقم الهاتف',
        fullName: 'الاسم الكامل',
        yourPosition: 'موقعك في الطابور',
        estWaitTime: '⏱️ وقت الانتظار المتوقع',
        youreInQueue: 'أنت في الطابور!',
        youreNext: '🎉 دورك التالي!',
        servedShortly: 'ستُخدَم قريباً',
        pleaseWait: 'يرجى انتظار دورك.',
        canClose: 'يمكنك إغلاق هذه الصفحة الآن.',
        poweredBy: 'مدعوم من',
        currentQueueStatus: 'الطابور الحالي',
        businessNotFound: 'المتجر غير موجود',
        businessNotFoundSub: 'المتجر الذي تبحث عنه غير موجود.',
        queueFullTitle: '⚠️ الطابور ممتلئ',
        queueFullSub: 'عذراً، وصلنا إلى الحد اليومي.',
        tryTomorrow: 'يرجى المحاولة مجدداً غداً.',

        businessSettings: 'إعدادات النشاط',
        businessSettingsSub: 'تحديث معلومات نشاطك التجاري',
        businessInfo: '🏢 معلومات النشاط',
        businessName: 'اسم النشاط التجاري',
        category: 'الفئة',
        city: 'المدينة',
        maxClients: 'الحد الأقصى للعملاء يومياً',
        maxClientsSub: 'ينطبق على الحجوزات المستقبلية فقط',
        saveSettings: '💾 حفظ الإعدادات',
        settingsSaved: '✅ تم حفظ الإعدادات!',
        digitalDisplay: '📺 شاشة العرض الرقمية',
        digitalDisplaySub: 'ضعها على تابلت أو شاشة للعملاء المنتظرين',
        openDisplay: '🖥️ فتح شاشة العرض',

        welcomeBack: 'مرحباً بعودتك',
        welcomeBackSub: 'سجل دخولك لإدارة طابورك',
        signIn: 'تسجيل الدخول',
        emailAddress: 'البريد الإلكتروني',
        password: 'كلمة المرور',
        forgotPassword: 'نسيت كلمة المرور؟',
        noAccount: 'ليس لديك حساب؟',
        createOne: 'أنشئ واحداً الآن',
        orDivider: 'أو',

        createAccount: 'إنشاء حساب',
        createAccountSub: 'ابدأ في إدارة طابورك اليوم',
        minChars: '٨ أحرف على الأقل',
        haveAccount: 'لديك حساب بالفعل؟',
        signInHere: 'تسجيل الدخول',
        registerSuccess: '✅ تم إنشاء الحساب! تحقق من بريدك الإلكتروني قبل تسجيل الدخول.',

        resetPassword: 'إعادة تعيين كلمة المرور',
        resetPasswordSub: 'أدخل بريدك لاستلام رابط إعادة التعيين',
        sendResetLink: 'إرسال الرابط',
        forgotSuccess: '✅ إذا كان الحساب موجوداً، فقد أُرسل رابط إعادة التعيين إلى بريدك.',

        newPassword: 'كلمة مرور جديدة',
        newPasswordSub: 'اختر كلمة مرور قوية',
        newPasswordLabel: 'كلمة المرور الجديدة',
        newPasswordPlaceholder: '٨ أحرف على الأقل',
        confirmPassword: 'تأكيد كلمة المرور',
        confirmPasswordPlaceholder: 'أعد كتابة كلمة المرور',
        updatePassword: 'تحديث كلمة المرور',
        resetSuccess: '✅ تم تحديث كلمة المرور. يمكنك تسجيل الدخول الآن.',
        goToLogin: '→ الذهاب لتسجيل الدخول',
        requestNewLink: 'طلب رابط جديد',

        createBusiness: 'إنشاء نشاطك التجاري',
        createBusinessSub: 'إعداد نظام إدارة الطابور',
        createBusinessBtn: 'إنشاء النشاط',
        businessNamePlaceholder: 'مثال: صالون النخبة',
        cityPlaceholder: 'مثال: الجزائر',
        selectCategory: 'اختر فئة',

        analyticsTitle: '📊 التحليلات',
        totalClients: 'إجمالي العملاء',
        thisWeek: 'هذا الأسبوع',
        avgServiceTimeLabel: 'متوسط وقت الخدمة',
        completionRate: 'معدل الإنجاز',
        skipRate: 'معدل التخطي',
        busiestDay: 'أكثر يوم ازدحاماً (30 يوم)',
        dailyClientsChart: '📆 العملاء اليوميون — آخر 7 أيام',
        peakHoursChart: '🕐 ساعات الذروة',
        last30days: 'آخر 30 يوماً',
        weeklyChart: '📈 الأداء الأسبوعي — آخر 4 أسابيع',
        allTimeStatus: '🍩 الحالة الإجمالية',
        allTimeStatusSub: 'تفصيل جميع الإدخالات',
        noDataYet: 'لا توجد بيانات بعد — ابدأ بإضافة عملاء.',
        noHourlyData: 'لا توجد بيانات ساعية بعد.',
        noWeeklyData: 'لا توجد بيانات أسبوعية بعد.',
        legendTotal: 'الإجمالي',
        legendDone: 'منجز',
        legendSkipped: 'متخطى',
        legendCompleted: 'مكتمل',
        analyticsRefresh: 'RendezVousDZ © 2026 · بيانات محدثة عند التحميل',

        barber: 'حلاق', salon: 'صالون تجميل', clinic: 'عيادة طبية',
        dentist: 'طبيب أسنان', spa: 'سبا وعافية', restaurant: 'مطعم', other: 'أخرى',

        monday: 'الاثنين', tuesday: 'الثلاثاء', wednesday: 'الأربعاء',
        thursday: 'الخميس', friday: 'الجمعة', saturday: 'السبت', sunday: 'الأحد',

        welcomeTitle: 'مرحباً في RendezVousDZ',
        welcomeSub: 'نظام إدارة الطابور الرقمي الاحترافي',
        getStarted: 'ابدأ الآن',
        featFastTitle: 'سريع وفعّال',
        featFastDesc: 'تبسيط تدفق عملائك مع إدارة الطابور في الوقت الفعلي',
        featEasyTitle: 'سهل الاستخدام',
        featEasyDesc: 'واجهة بديهية مصممة لتجربة مستخدم سلسة',
        featSecureTitle: 'آمن وموثوق',
        featSecureDesc: 'بياناتك محمية بأمان على مستوى المؤسسات',

        footer: 'RendezVousDZ © 2026 - نظام إدارة الطابور الاحترافي',
    }
};

function getCurrentLang() {
    const s = localStorage.getItem(LANG_KEY) || 'en';
    return SUPPORTED_LANGS.includes(s) ? s : 'en';
}

function t(key) {
    const lang = getCurrentLang();
    return (TRANSLATIONS[lang] && TRANSLATIONS[lang][key]) || TRANSLATIONS.en[key] || key;
}

function _applyLanguage(lang) {
    if (!SUPPORTED_LANGS.includes(lang)) return;
    localStorage.setItem(LANG_KEY, lang);

    // RTL / LTR
    if (lang === 'ar') {
        document.documentElement.setAttribute('dir', 'rtl');
        document.documentElement.setAttribute('lang', 'ar');
    } else {
        document.documentElement.removeAttribute('dir');
        document.documentElement.setAttribute('lang', lang);
    }

    // Translate all [data-i18n] elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const val = (TRANSLATIONS[lang] && TRANSLATIONS[lang][key]) || TRANSLATIONS.en[key] || key;
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            if (el.hasAttribute('placeholder')) el.setAttribute('placeholder', val);
        } else if (el.tagName === 'OPTION') {
            el.textContent = val;
        } else {
            el.textContent = val;
        }
    });

    // Translate placeholders separately via [data-i18n-ph]
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
        const key = el.getAttribute('data-i18n-ph');
        const val = (TRANSLATIONS[lang] && TRANSLATIONS[lang][key]) || TRANSLATIONS.en[key] || key;
        el.setAttribute('placeholder', val);
    });

    // Mark active lang button
    document.querySelectorAll('.lang-picker button').forEach(btn => {
        btn.classList.toggle('lang-active', btn.dataset.lang === lang);
    });
}

function switchLanguage(lang) {
    _applyLanguage(lang);
}

window.switchLanguage = switchLanguage;
window.getCurrentLang = getCurrentLang;
window.t = t;


// ═══════════════════════════════════════════════════════
// 🚀 INIT (runs after DOM ready)
// ═══════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', function () {
    // Theme (re-apply to also swap logos now that DOM is ready)
    _applyTheme(localStorage.getItem(THEME_KEY) || 'light');

    // Language
    _applyLanguage(getCurrentLang());

    initAnimations();
    initFormValidation();
    initPasswordToggle();
    initQueueUpdates();
    initNotifications();
    initThemeEffects();
    initRealtimeQueue();
});


// ═══════════════════════════════════════════════════════
// 🔥 REAL-TIME QUEUE UPDATES via Socket.IO
// ═══════════════════════════════════════════════════════
function initRealtimeQueue() {
    const businessId = getBusinessIdFromPage();
    if (!businessId) return;

    const script   = document.createElement('script');
    script.src     = 'https://cdn.socket.io/4.5.4/socket.io.min.js';
    script.onload  = () => connectToRealtimeQueue(businessId);
    script.onerror = () => console.error('❌ Failed to load Socket.IO');
    document.head.appendChild(script);
}

function getBusinessIdFromPage() {
    const btn = document.querySelector('a[href^="/b/"]');
    if (btn) {
        const m = btn.getAttribute('href').match(/\/b\/(\d+)/);
        return m ? m[1] : null;
    }
    const m = window.location.pathname.match(/\/b\/(\d+)/);
    return m ? m[1] : null;
}

function connectToRealtimeQueue(businessId) {
    const socket = io();
    socket.on('connect',       () => socket.emit('join', { business_id: businessId }));
    socket.on('queue_updated', data => { if (data.business_id == businessId) updateQueueDisplay(data); });
    socket.on('disconnect',    () => console.log('❌ Real-time disconnected'));
}

function updateQueueDisplay(data) {
    const currentCountEl = document.querySelector('.stat-value');
    if (currentCountEl && currentCountEl.textContent !== data.current_count.toString()) {
        currentCountEl.textContent = data.current_count;
        animateElement(currentCountEl);
    }

    const statCards = document.querySelectorAll('.stat-card');
    if (statCards.length >= 3) {
        const remainingEl = statCards[2].querySelector('.stat-value');
        if (remainingEl) {
            remainingEl.textContent = data.max_clients - data.current_count;
            remainingEl.style.color = data.queue_full ? 'var(--error)' : 'var(--success)';
            animateElement(remainingEl);
        }
    }

    const queueCountEl = document.querySelector('.queue-count');
    if (queueCountEl) {
        queueCountEl.textContent = `${data.current_count}/${data.max_clients}`;
        animateElement(queueCountEl);
    }

    const queueFullAlert = document.querySelector('[data-queue-full-alert]');
    if (data.queue_full && !queueFullAlert && window.location.pathname.includes('/dashboard')) {
        const statsGrid = document.querySelector('.stats-grid');
        if (statsGrid) {
            const alert = document.createElement('div');
            alert.setAttribute('data-queue-full-alert', '1');
            alert.style.cssText = 'background:rgba(239,68,68,0.1);border:2px solid var(--error);border-radius:var(--radius-lg);padding:var(--space-lg);margin-bottom:var(--space-xl);text-align:center;';
            alert.innerHTML = `<p style="color:var(--error);font-weight:700;font-size:1.125rem;margin:0;">⚠️ Queue Full - Daily limit reached (${data.max_clients}/${data.max_clients})</p>`;
            statsGrid.after(alert);
        }
    } else if (!data.queue_full && queueFullAlert) {
        queueFullAlert.remove();
    }

    if (window.location.pathname.includes('/dashboard')) {
        updateQueueList(data.queue_entries);
    }

    if (window.location.pathname.includes('/b/')) {
        const statusStrong = document.querySelector('.queue-status-count');
        if (statusStrong) statusStrong.textContent = `${data.current_count}/${data.max_clients}`;

        const submitBtn = document.querySelector('button[type="submit"]');
        const inputs    = document.querySelectorAll('input[name="client_name"], input[name="client_phone"]');
        if (data.queue_full) {
            if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = t('queueFull'); }
            inputs.forEach(i => i.disabled = true);
        } else {
            if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = t('joinQueue'); }
            inputs.forEach(i => i.disabled = false);
        }
    }
}

function updateQueueList(entries) {
    const queueList  = document.querySelector('.queue-list');
    const emptyState = document.querySelector('.empty-state');

    if (!entries || entries.length === 0) {
        if (queueList) queueList.style.display = 'none';
        if (!emptyState) {
            const section = document.querySelector('.queue-section');
            if (section) {
                const empty = document.createElement('div');
                empty.className = 'empty-state';
                empty.innerHTML = '<div class="empty-state-icon">📋</div><h4>No clients in queue</h4><p>Add a client above to get started</p>';
                section.appendChild(empty);
            }
        }
        return;
    }

    if (emptyState) emptyState.style.display = 'none';
    if (!queueList) return;
    queueList.style.display = 'flex';

    queueList.innerHTML = entries.map((entry, i) => `
        <div class="queue-item" style="animation:slideInLeft 0.4s ease-out both;">
            <div class="queue-number">#${i + 1}</div>
            <div class="queue-details">
                <div class="queue-name">${escapeHtml(entry.client_name)}</div>
                <div class="queue-meta">
                    <span class="queue-status status-${entry.status}">${capitalizeFirst(entry.status)}</span>
                    ${entry.client_phone ? `<span class="queue-time">📞 ${escapeHtml(entry.client_phone)}</span>` : ''}
                </div>
            </div>
            <div class="queue-actions">
                ${entry.status === 'waiting' ? `
                    <a href="/mark-done/${entry.id}" class="btn btn-success">${t('markDone')}</a>
                    <a href="/mark-skipped/${entry.id}" class="btn btn-ghost">${t('skip')}</a>
                ` : ''}
            </div>
        </div>`).join('');
}


// ═══════════════════════════════════════════════════════
// ANIMATIONS
// ═══════════════════════════════════════════════════════
function initAnimations() {
    const observer = new IntersectionObserver(entries => {
        entries.forEach(e => {
            if (e.isIntersecting) {
                e.target.style.animation = 'fadeIn 0.5s ease-out both';
                observer.unobserve(e.target);
            }
        });
    }, { threshold: 0.1 });
    document.querySelectorAll('.card, .stat-card, .feature-card').forEach(c => observer.observe(c));
}

function animateElement(el) {
    el.style.animation = 'none';
    el.offsetHeight;
    el.style.animation = 'pulse 0.4s ease-out';
}


// ═══════════════════════════════════════════════════════
// FORM VALIDATION
// ═══════════════════════════════════════════════════════
function initFormValidation() {
    document.querySelectorAll('form').forEach(form => {
        form.querySelectorAll('input[required], select[required]').forEach(input => {
            input.addEventListener('blur', () => validateField(input));
            input.addEventListener('input', () => {
                if (input.classList.contains('input-error')) validateField(input);
            });
        });
    });
}

function validateField(input) {
    if (!input.value.trim()) { showError(input, 'This field is required'); return false; }
    if (input.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value)) {
        showError(input, 'Please enter a valid email address'); return false;
    }
    if (input.type === 'password' && input.value.length < 8) {
        showError(input, 'Password must be at least 8 characters'); return false;
    }
    removeError(input);
    return true;
}

function showError(input, message) {
    input.classList.add('input-error');
    input.style.borderColor = 'var(--error)';
    const parent = input.parentElement;
    const existing = parent.querySelector('.field-error');
    if (existing) existing.remove();
    const err = document.createElement('span');
    err.className = 'field-error';
    err.style.cssText = 'color:var(--error);font-size:0.8rem;margin-top:0.25rem;display:block;';
    err.textContent = message;
    parent.appendChild(err);
}

function removeError(input) {
    input.classList.remove('input-error');
    input.style.borderColor = '';
    const err = input.parentElement.querySelector('.field-error');
    if (err) err.remove();
}


// ═══════════════════════════════════════════════════════
// PASSWORD TOGGLE
// ═══════════════════════════════════════════════════════
function initPasswordToggle() {
    document.querySelectorAll('input[type="password"]').forEach(input => {
        const wrapper = input.parentElement;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'password-toggle';
        btn.innerHTML = '👁️';
        btn.setAttribute('aria-label', 'Toggle password visibility');
        wrapper.style.position = 'relative';
        wrapper.appendChild(btn);
        btn.addEventListener('click', function () {
            input.type = input.type === 'password' ? 'text' : 'password';
            this.innerHTML = input.type === 'password' ? '👁️' : '🙈';
        });
    });
}


// ═══════════════════════════════════════════════════════
// QUEUE ITEM ANIMATIONS
// ═══════════════════════════════════════════════════════
function initQueueUpdates() {
    document.querySelectorAll('.queue-item').forEach((item, i) => {
        item.style.animation = `slideInLeft 0.4s ease-out ${i * 0.1}s both`;
    });
}


// ═══════════════════════════════════════════════════════
// NOTIFICATIONS
// ═══════════════════════════════════════════════════════
function initNotifications() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('success')) showNotification(params.get('success'), 'success');
    if (params.get('error'))   showNotification(params.get('error'),   'error');
}

function showNotification(message, type = 'info') {
    const n = document.createElement('div');
    n.style.cssText = `position:fixed;top:20px;right:20px;background:var(--surface-card);padding:1rem 1.5rem;
        border-radius:var(--radius-lg);box-shadow:var(--shadow-xl);z-index:9999;display:flex;
        align-items:center;gap:0.75rem;max-width:400px;animation:slideInRight 0.3s ease-out;
        border-left:4px solid ${type==='success'?'var(--success)':type==='error'?'var(--error)':'var(--info)'};`;
    const icon = type==='success' ? '✅' : type==='error' ? '❌' : 'ℹ️';
    n.innerHTML = `<span style="font-size:1.5rem;">${icon}</span>
        <span style="font-weight:500;color:var(--text-primary);">${message}</span>
        <button onclick="this.parentElement.remove()" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:1.25rem;margin-left:auto;">×</button>`;
    document.body.appendChild(n);
    setTimeout(() => {
        n.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => n.remove(), 300);
    }, 5000);
}


// ═══════════════════════════════════════════════════════
// THEME EFFECTS
// ═══════════════════════════════════════════════════════
function initThemeEffects() {
    document.querySelectorAll('.btn-primary, .btn-secondary').forEach(btn => {
        btn.addEventListener('mousemove', function (e) {
            const r = this.getBoundingClientRect();
            this.style.setProperty('--mouse-x', `${e.clientX - r.left}px`);
            this.style.setProperty('--mouse-y', `${e.clientY - r.top}px`);
        });
    });
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth' }); }
        });
    });
}


// ═══════════════════════════════════════════════════════
// UTILS
// ═══════════════════════════════════════════════════════
function escapeHtml(str) {
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(str));
    return d.innerHTML;
}

function capitalizeFirst(s) {
    return s.charAt(0).toUpperCase() + s.slice(1);
}

window.RendezVousDZ = { showNotification, toggleTheme, switchLanguage };

// Extra keyframes
const _style = document.createElement('style');
_style.textContent = `
    @keyframes slideOutRight { from{opacity:1;transform:translateX(0)} to{opacity:0;transform:translateX(100%)} }
    @keyframes pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.05)} }
`;
document.head.appendChild(_style);
