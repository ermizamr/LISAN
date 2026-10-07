package com.example.ethiopian_translator

import android.speech.tts.TextToSpeech
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.util.Locale

class MainActivity : FlutterActivity(), TextToSpeech.OnInitListener {
    private val CHANNEL = "com.example.ethiopian_translator/tts"
    private var tts: TextToSpeech? = null
    private var isTtsReady = false
    private var isGoogleTts = false

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        initTts()

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "speak" -> {
                    val text = call.argument<String>("text") ?: ""
                    val lang = call.argument<String>("lang") ?: "en"
                    if (isTtsReady && text.isNotEmpty()) {
                        val locale = when (lang) {
                            "amh" -> Locale("am", "ET")
                            "orm" -> Locale("om", "ET")
                            "tir" -> Locale("ti", "ET")
                            "som" -> Locale("so", "SO")
                            else -> Locale.US
                        }
                        tts?.language = locale
                        val speakStatus = tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "lisan_utterance")
                        result.success(speakStatus == TextToSpeech.SUCCESS)
                    } else {
                        result.success(false)
                    }
                }
                "stop" -> {
                    tts?.stop()
                    result.success(true)
                }
                else -> result.notImplemented()
            }
        }
    }

    private fun initTts() {
        try {
            // First attempt to initialize Google TTS (com.google.android.tts) for high quality Amharic & English
            tts = TextToSpeech(this, this, "com.google.android.tts")
            isGoogleTts = true
        } catch (e: Exception) {
            try {
                tts = TextToSpeech(this, this)
                isGoogleTts = false
            } catch (ex: Exception) {
                ex.printStackTrace()
            }
        }
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            isTtsReady = true
        } else if (isGoogleTts) {
            // If Google TTS engine failed to init, gracefully fallback to default system TTS
            try {
                isGoogleTts = false
                tts = TextToSpeech(this) { fallbackStatus ->
                    if (fallbackStatus == TextToSpeech.SUCCESS) {
                        isTtsReady = true
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    override fun onDestroy() {
        tts?.stop()
        tts?.shutdown()
        super.onDestroy()
    }
}
