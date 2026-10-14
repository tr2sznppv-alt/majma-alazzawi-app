# Add project specific ProGuard rules here.
# You can control the set of applied configuration files using the
# proguardFiles setting in build.gradle.
#
# For more details, see
#   http://developer.android.com/guide/developing/tools/proguard.html

# If your project uses WebView with JS, uncomment the following
# and specify the fully qualified class name to the JavaScript interface
# class:
#-keepclassmembers class fqcn.of.javascript.interface.for.webview {
#   public *;
#}

# Uncomment this to preserve the line number information for
# debugging stack traces.
#-keepattributes SourceFile,LineNumberTable

# If you keep the line number information, uncomment this to
# hide the original source file name.
#-renamesourcefileattribute SourceFile


# ═══════════════════════════════════════════════════════
# Capacitor Core
# ═══════════════════════════════════════════════════════
-keep class com.getcapacitor.** { *; }
-keep @com.getcapacitor.annotation.CapacitorPlugin class * { *; }
-keep public class * extends com.getcapacitor.Plugin { *; }
-keepclassmembers class * extends com.getcapacitor.Plugin {
    @com.getcapacitor.PluginMethod public <methods>;
}

# ═══════════════════════════════════════════════════════
# Capacitor Plugins
# ═══════════════════════════════════════════════════════
-keep class com.capacitorjs.plugins.** { *; }
-keep class com.ryltsov.alex.plugins.file.opener.** { *; }

# ═══════════════════════════════════════════════════════
# WebView JavaScript Interface
# ═══════════════════════════════════════════════════════
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# ═══════════════════════════════════════════════════════
# AndroidX
# ═══════════════════════════════════════════════════════
-keep class androidx.** { *; }
-dontwarn androidx.**

# ═══════════════════════════════════════════════════════
# عام
# ═══════════════════════════════════════════════════════
-keepattributes *Annotation*
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile
