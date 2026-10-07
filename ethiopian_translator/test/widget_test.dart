import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';

import 'package:ethiopian_translator/main.dart';
import 'package:ethiopian_translator/lisan_icons.dart';
import 'package:ethiopian_translator/recording_service.dart';

void main() {
  testWidgets('translator shell renders and navigates full Figma flow', (
    WidgetTester tester,
  ) async {
    tester.view.physicalSize = const Size(800, 1200);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() => tester.view.resetPhysicalSize());

    await tester.pumpWidget(const TranslatorApp(
      audioCapture: DemoRecordingService(),
    ));

    // 1. Ready state verification
    expect(find.text('Lisan'), findsOneWidget);
    expect(find.text('Settings'), findsOneWidget);
    expect(find.text('Type text'), findsOneWidget);
    expect(find.textContaining('Speak freely.'), findsOneWidget);

    // 2. Open Type Text modal dialog
    await tester.tap(find.text('Type text'));
    await tester.pumpAndSettle();
    expect(find.text('TEXT TRANSLATION'), findsOneWidget);

    // 3. Cancel Type Text dialog -> Return to Ready
    await tester.tap(find.byIcon(Icons.close));
    await tester.pumpAndSettle();
    expect(find.textContaining('Speak freely.'), findsOneWidget);

    // 4. Tap Settings -> Settings view
    await tester.tap(find.text('Settings'));
    await tester.pumpAndSettle();
    expect(find.text('PERSONALIZE LISAN'), findsOneWidget);
    expect(find.text('Advanced\nsettings'), findsOneWidget);
    expect(find.text('Translate into'), findsOneWidget);
    expect(find.text('Automatic two-way translation'), findsOneWidget);

    // 5. Tap Close -> Return to Ready
    final closeFinder = find.byWidgetPredicate(
      (w) => w is LisanIcon && w.type == LisanIconType.close,
    );
    expect(closeFinder, findsOneWidget);
    await tester.tap(closeFinder);
    await tester.pumpAndSettle();
    expect(find.textContaining('Speak freely.'), findsOneWidget);
    expect(find.text('HOLD TO SPEAK'), findsOneWidget);
  });

  testWidgets('mic dial behaves as strict hold-to-talk (no touch-toggle)', (
    WidgetTester tester,
  ) async {
    tester.view.physicalSize = const Size(800, 1200);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() => tester.view.resetPhysicalSize());

    await tester.pumpWidget(const TranslatorApp(
      audioCapture: DemoRecordingService(),
    ));

    final dialFinder = find.byKey(const ValueKey('mic_dial_button'));
    expect(dialFinder, findsOneWidget);
    expect(find.text('HOLD TO SPEAK'), findsOneWidget);

    // 1. Press and hold down
    final gesture = await tester.startGesture(tester.getCenter(dialFinder));
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.text('RECORDING · RELEASE TO TRANSLATE'), findsOneWidget);

    // 2. Release after holding
    await gesture.up();
    await tester.pumpAndSettle();
    // After release, finishes recording
    expect(find.text('RECORDING · RELEASE TO TRANSLATE'), findsNothing);
  });

  testWidgets('releasing mic dial immediately opens Translate into modal without lag', (
    WidgetTester tester,
  ) async {
    tester.view.physicalSize = const Size(800, 1200);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() => tester.view.resetPhysicalSize());

    await tester.pumpWidget(const TranslatorApp(
      audioCapture: DemoRecordingService(),
      minHoldDuration: Duration.zero,
    ));

    final dialFinder = find.byKey(const ValueKey('mic_dial_button'));

    // 1. Press and hold down
    final gesture = await tester.startGesture(tester.getCenter(dialFinder));
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.text('RECORDING · RELEASE TO TRANSLATE'), findsOneWidget);

    // 2. Release dial -> INSTANTLY pops up the target language picker
    await gesture.up();
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 350));

    expect(find.text('Translate into'), findsOneWidget);
    expect(find.text('VOICE CAPTURED · SELECT TARGET'), findsOneWidget);
    expect(find.text('መተርጎሚያ ቋንቋ ይምረጡ'), findsOneWidget);

    // 3. Tapping target language proceeds to translation
    await tester.tap(find.text('English'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 350));
    expect(find.text('Translate into'), findsNothing);
  });
}
