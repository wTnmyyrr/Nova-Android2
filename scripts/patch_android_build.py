from pathlib import Path
p = Path("/tmp/nova-src/NOVA_v4.0_Complete/app/src/main/assets/index.html")
s = p.read_text(encoding="utf-8")
marker = "state = { ...state, ...JSON.parse(localStorage.getItem(settingsKey) || '{}') };\n} catch {}"
assert marker in s, 'Could not find NOVA settings initialization marker'
s = s.replace(marker, marker + "\n// Preconfigured NOVA Cloudflare AI backend\nif (!state.backendUrl) state.backendUrl = 'https://nova-ai-brain.hy1009568.workers.dev';", 1)
# Native Android voice + external-app actions (file:// WebView has no Web Speech API).
bridge = Path("/tmp/nova-src/NOVA_v4.0_Complete/app/src/main/java/com/nova/companion/NovaAndroidBridge.kt")
bridge.write_text("""package com.nova.companion

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import android.speech.RecognizerIntent
import android.speech.tts.TextToSpeech
import android.webkit.JavascriptInterface
import android.widget.Toast
import java.util.Locale

class NovaAndroidBridge(private val context: Context) : TextToSpeech.OnInitListener {
    private var tts: TextToSpeech = TextToSpeech(context, this)
    private var ttsReady = false
    private val packageMap = mapOf(
        "youtube" to "com.google.android.youtube", "whatsapp" to "com.whatsapp",
        "instagram" to "com.instagram.android", "spotify" to "com.spotify.music",
        "google maps" to "com.google.android.apps.maps", "gmail" to "com.google.android.gm",
        "telegram" to "org.telegram.messenger", "amazon" to "in.amazon.mShop.android.shopping",
        "flipkart" to "com.flipkart.android", "play store" to "com.android.vending"
    )
    override fun onInit(status: Int) { ttsReady = status == TextToSpeech.SUCCESS }
    @JavascriptInterface fun speak(text: String, language: String) {
        if (!ttsReady) return
        val locale = if (language == "en") Locale("en", "IN") else Locale("hi", "IN")
        tts.language = locale
        tts.setSpeechRate(0.94f)
        tts.setPitch(1.12f)
        if (Build.VERSION.SDK_INT >= 21) tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "nova_reply")
        else @Suppress("DEPRECATION") tts.speak(text, TextToSpeech.QUEUE_FLUSH, null)
    }
    @JavascriptInterface fun stopSpeaking() { if (ttsReady) tts.stop() }
    @JavascriptInterface fun startVoiceInput(language: String) {
        (context as? MainActivity)?.startNovaVoiceRecognition(language)
    }
    @JavascriptInterface fun openUrl(url: String) {
        try {
  val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
  context.startActivity(intent)
        } catch (_: Exception) { Toast.makeText(context, "App/link open nahi ho paya", Toast.LENGTH_SHORT).show() }
    }
    @JavascriptInterface fun openApp(appKey: String): Boolean {
        val pkg = packageMap[appKey.lowercase().trim()] ?: return false
        val i = context.packageManager.getLaunchIntentForPackage(pkg) ?: return false
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK); context.startActivity(i); return true
    }
    @JavascriptInterface fun startWakeWordService() {
        val i = Intent(context, NovaWakeWordService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) context.startForegroundService(i) else context.startService(i)
    }
    @JavascriptInterface fun stopWakeWordService() { context.stopService(Intent(context, NovaWakeWordService::class.java)) }
    @JavascriptInterface fun toggleFloatingBubble() {
        if (!Settings.canDrawOverlays(context)) {
  Toast.makeText(context, "Please allow Display over other apps for NOVA", Toast.LENGTH_LONG).show()
  context.startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:${context.packageName}")).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
  return
        }
        context.startService(Intent(context, NovaFloatingOverlayService::class.java))
    }
}
""", encoding="utf-8")
activity = Path("/tmp/nova-src/NOVA_v4.0_Complete/app/src/main/java/com/nova/companion/MainActivity.kt")
activity.write_text("""package com.nova.companion

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.speech.RecognizerIntent
import android.webkit.*
import androidx.activity.ComponentActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import org.json.JSONObject

class MainActivity : ComponentActivity() {
    private lateinit var webView: WebView
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED)
  ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.RECORD_AUDIO), 100)
        webView = WebView(this)
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true
        webView.settings.mediaPlaybackRequiresUserGesture = false
        webView.settings.allowFileAccess = true
        webView.webChromeClient = object : WebChromeClient() {
  override fun onPermissionRequest(request: PermissionRequest) { runOnUiThread { request.grant(request.resources) } }
        }
        webView.webViewClient = object : WebViewClient() {
  override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
      val url = request?.url?.toString() ?: return false
      if (url.startsWith("file:///android_asset/")) return false
      try { startActivity(Intent(Intent.ACTION_VIEW, android.net.Uri.parse(url))) } catch (_: Exception) {}
      return true
  }
        }
        webView.addJavascriptInterface(NovaAndroidBridge(this), "NovaAndroidBridge")
        setContentView(webView)
        webView.loadUrl("file:///android_asset/index.html")
    }
    fun startNovaVoiceRecognition(language: String) {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
  ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.RECORD_AUDIO), 100)
  return
        }
        try {
  val i = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
      putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
      putExtra(RecognizerIntent.EXTRA_LANGUAGE, if (language == "en") "en-IN" else "hi-IN")
      putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, if (language == "en") "en-IN" else "hi-IN")
      putExtra(RecognizerIntent.EXTRA_PROMPT, "NOVA sun rahi hai, boliye…")
  }
  startActivityForResult(i, 2026)
        } catch (_: Exception) {
  webView.evaluateJavascript("window.onNovaSpeechError && window.onNovaSpeechError()", null)
        }
    }
    @Deprecated("Deprecated in Android")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 2026) {
  val spoken = if (resultCode == RESULT_OK) data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)?.firstOrNull() else null
  val js = if (spoken.isNullOrBlank()) "window.onNovaSpeechError && window.onNovaSpeechError()" else "window.onNovaSpeechResult && window.onNovaSpeechResult(${JSONObject.quote(spoken)})"
  webView.evaluateJavascript(js, null)
        }
    }
    @Deprecated("Deprecated in Android")
    override fun onBackPressed() { if (::webView.isInitialized && webView.canGoBack()) webView.goBack() else super.onBackPressed() }
}
""", encoding="utf-8")
# Route speech through Android TextToSpeech; route speech input through Android recognizer.
old = "  if (!('speechSynthesis' in window)) return;\n  if (forceAuto && !state.autoSpeak) return;"
new = "  if (forceAuto && !state.autoSpeak) return;\n  if (window.NovaAndroidBridge) { if (isSpeaking) { window.NovaAndroidBridge.stopSpeaking(); } window.NovaAndroidBridge.speak(cleanSpeechText(text), lang === 'en' ? 'en' : 'hi'); isSpeaking = true; avatar.classList.add('speaking'); setTimeout(() => { isSpeaking = false; avatar.classList.remove('speaking'); }, Math.max(1800, String(text || '').length * 65)); return; }\n  if (!('speechSynthesis' in window)) return;"
assert old in s, "toggleSpeak entry not found"
# Define sanitizer before toggleSpeak and use it for native voice.
s = s.replace("function toggleSpeak(text, lang = 'hinglish'", "function cleanSpeechText(text) { return (text || '').replace(/https?:\\/\\/\\S+/g, '').replace(/[\\u{1F300}-\\u{1FAFF}]/gu, '').replace(/\\s+/g, ' ').trim(); }\n\nfunction toggleSpeak(text, lang = 'hinglish'", 1)
s = s.replace(old, new, 1)
s = s.replace("  if ('speechSynthesis' in window) speechSynthesis.cancel();", "  if (window.NovaAndroidBridge) window.NovaAndroidBridge.stopSpeaking();\n  if ('speechSynthesis' in window) speechSynthesis.cancel();", 1)
mic_start = "  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;\n  if (!SR || window.location.protocol === 'file:') {"
native_mic = """  if (window.NovaAndroidBridge) {
    isListening = true; micBtn.classList.add('listening');
    setAvatarState('listening', '🎙️', '🎙️ Sun rahi hoon…');
    hint.textContent = '🎙️ Boliye, NOVA sun rahi hai…';
    window.onNovaSpeechResult = transcript => { isListening = false; micBtn.classList.remove('listening'); input.value = transcript; send(); };
    window.onNovaSpeechError = () => { isListening = false; micBtn.classList.remove('listening'); hint.textContent = '⚠️ Voice input cancel hua ya available nahi hai.'; };
    window.NovaAndroidBridge.startVoiceInput(state.lang === 'en' ? 'en' : 'hi');
    return;
  }
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR || window.location.protocol === 'file:') {"""
assert mic_start in s, "mic handler marker not found"
s = s.replace(mic_start, native_mic, 1)
# Native app opens for action links (YouTube/song/search/maps).
s = s.replace("    link.href = actionUrl;\n    link.target = '_blank';", "    link.href = actionUrl;\n    link.target = '_blank';\n    if (window.NovaAndroidBridge) link.onclick = ev => { ev.preventDefault(); window.NovaAndroidBridge.openUrl(actionUrl); };", 1)
p.write_text(s, encoding="utf-8")
print("Patched native TTS, Android speech recognition, and external app/link launching")


# Native YouTube autoplay, flashlight/camera commands, and remove Android title bar.
from pathlib import Path as P
root = P("/tmp/nova-src/NOVA_v4.0_Complete")
hp = root / "app/src/main/assets/index.html"
s = hp.read_text(encoding="utf-8")
old = """  if (/\\b(flashlight|torch|flash light)\\b/i.test(lower)) {
    return { reply: '🔦 Browser se hardware torch directly control nahi hoti — Android CameraManager API ke saath Native APK mein chalegi.' };
  }"""
new = """  if (/\\b(flashlight|torch|flash light)\\b/i.test(lower)) {
    const off = /\\b(off|band|disable)\\b/i.test(lower);
    if (window.NovaAndroidBridge) {
      const ok = window.NovaAndroidBridge.toggleTorch(!off);
      return { reply: ok ? (off ? '🔦 Torch band kar di ✓' : '🔦 Torch on kar di ✓') : '⚠️ Torch unavailable hai; Camera permission allow karein.' };
    }
    return { reply: '⚠️ Torch ke liye NOVA Android app chahiye.' };
  }
  if (/\\b(open camera|camera kholo|camera khol|take photo|photo lo|selfie lo|camera)\\b/i.test(lower)) {
    if (window.NovaAndroidBridge) { window.NovaAndroidBridge.openCamera(); return { reply: '📷 Camera khol diya ✓' }; }
    return { reply: '⚠️ Camera ke liye NOVA Android app chahiye.' };
  }"""
if old in s: s = s.replace(old, new, 1)
elif "toggleTorch(!off)" not in s: raise SystemExit("Torch command marker missing")
needle = "    const watchUrl = " + chr(96) + "https://www.youtube.com/watch?v=" + chr(36) + "{picked.id}" + chr(96) + ";"
if needle in s and "playYouTube(watchUrl)" not in s:
    s = s.replace(needle, needle + "\n    if (window.NovaAndroidBridge) window.NovaAndroidBridge.playYouTube(watchUrl);", 1)
    s = s.replace("YouTube par kholne ke liye neeche button tap karein.", "YouTube par gaana play kar rahi hoon…", 1)
hp.write_text(s, encoding="utf-8")

bp = root / "app/src/main/java/com/nova/companion/NovaAndroidBridge.kt"
b = bp.read_text(encoding="utf-8")
marker = "    @JavascriptInterface fun openApp(appKey: String): Boolean {"
methods = '''    @JavascriptInterface
    fun playYouTube(url: String) {
        try {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url)).setPackage("com.google.android.youtube")
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(intent)
        } catch (_: Exception) { openUrl(url) }
    }
    @JavascriptInterface
    fun openUrl(url: String) {
        try { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
        catch (_: Exception) { Toast.makeText(context, "App/link nahi khul paya", Toast.LENGTH_SHORT).show() }
    }
    @JavascriptInterface
    fun toggleTorch(enabled: Boolean): Boolean {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M) return false
        return try {
            val manager = context.getSystemService(Context.CAMERA_SERVICE) as android.hardware.camera2.CameraManager
            val id = manager.cameraIdList.firstOrNull {
                manager.getCameraCharacteristics(it).get(android.hardware.camera2.CameraCharacteristics.FLASH_INFO_AVAILABLE) == true
            } ?: return false
            manager.setTorchMode(id, enabled)
            true
        } catch (_: SecurityException) {
            (context as? MainActivity)?.requestCameraPermission()
            false
        } catch (_: Exception) { false }
    }
    @JavascriptInterface
    fun openCamera() {
        try { context.startActivity(Intent(android.provider.MediaStore.ACTION_IMAGE_CAPTURE).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
        catch (_: Exception) { Toast.makeText(context, "Camera app nahi mili", Toast.LENGTH_SHORT).show() }
    }

'''
if "fun playYouTube(url: String)" not in b:
    if marker not in b: raise SystemExit("Bridge insertion marker missing")
    b = b.replace(marker, methods + marker, 1)
bp.write_text(b, encoding="utf-8")

ap = root / "app/src/main/java/com/nova/companion/MainActivity.kt"
a = ap.read_text(encoding="utf-8")
if "fun requestCameraPermission()" not in a:
    insert = '''    fun requestCameraPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED)
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.CAMERA), 303)
    }
'''
    marker = '    @Deprecated("Deprecated in Android")'
    if marker not in a: raise SystemExit("Activity insertion marker missing")
    a = a.replace(marker, insert + marker, 1)
ap.write_text(a, encoding="utf-8")

mp = root / "app/src/main/AndroidManifest.xml"
m = mp.read_text(encoding="utf-8")
if "android.permission.CAMERA" not in m:
    m = m.replace('    <uses-permission android:name="android.permission.RECORD_AUDIO" />', '    <uses-permission android:name="android.permission.RECORD_AUDIO" />\n    <uses-permission android:name="android.permission.CAMERA" />\n    <uses-feature android:name="android.hardware.camera" android:required="false" />')
m = m.replace('android:label="NOVA AI Companion"', 'android:label="NOVA"')
if 'android:theme="@android:style/Theme.Material.Light.NoActionBar"' not in m:
    m = m.replace('<application\n', '<application\n        android:theme="@android:style/Theme.Material.Light.NoActionBar"\n')
mp.write_text(m, encoding="utf-8")
print("Patched direct YouTube playback, torch/camera commands, and hidden app title bar")
