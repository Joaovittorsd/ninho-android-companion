plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.ninho.companion"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.ninho.companion"
        // minSdk 26 (Android 8.0): modern baseline for Device Owner QR provisioning
        // + the FCM/WorkManager/background-execution APIs the full app will need later.
        // Revisit alongside Open Question 2 in the design doc (target device fleet).
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0-qr-provisioning-spike"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        viewBinding = false
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
}
