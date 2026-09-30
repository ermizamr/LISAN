import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ethiopian_translator/main.dart';

void main() {
  testWidgets('translator shell renders and navigates full Figma flow', (
    WidgetTester tester,
  ) async {
    tester.view.physicalSize = const Size(800, 1200);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() => tester.view.resetPhysicalSize());

    await tester.pumpWidget(const TranslatorApp());

    // 1. Ready state verification
    expect(find.text('Lisan'), findsOneWidget);
    expect(find.text('Advanced settings'), findsOneWidget);
    expect(find.text('VOICE TRANSLATOR'), findsOneWidget);
    expect(find.textContaining('Speak freely.'), findsOneWidget);

    // 2. Press dial -> Speaking state
    final dialFinder = find.byKey(const ValueKey('mic_dial_button'));
    final gesture = await tester.startGesture(tester.getCenter(dialFinder));
    await tester.pump();
    expect(find.text('LISTENING NOW'), findsOneWidget);
    expect(find.text('I’m listening…'), findsOneWidget);

    // 3. Release dial -> Language selection sheet
    await gesture.up();
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pumpAndSettle();

    expect(find.text('WE HEARD YOU'), findsOneWidget);
    expect(find.text('Which language\ndid you speak?'), findsOneWidget);
    expect(find.text('አማርኛ'), findsOneWidget);
    expect(find.text('ትግርኛ'), findsOneWidget);
    expect(find.text('Soomaali'), findsOneWidget);
    expect(find.text('Afaan Oromoo'), findsNWidgets(2));

    // 4. Tap Amharic card -> Result screen
    await tester.tap(find.text('አማርኛ'));
    await tester.pump();
    await tester.pump(const Duration(seconds: 4));
    await tester.pumpAndSettle();

    expect(find.text('TRANSLATION READY'), findsOneWidget);
    expect(find.text('You’re understood.'), findsOneWidget);
    expect(find.text('TRANSLATION OUTPUT'), findsOneWidget);
    expect(find.text('Verified Memory'), findsOneWidget);
    expect(find.text('Speak again'), findsOneWidget);

    // 5. Tap Speak again -> Returns to ready
    await tester.tap(find.text('Speak again'));
    await tester.pumpAndSettle();
    expect(find.text('VOICE TRANSLATOR'), findsOneWidget);

    // 6. Tap Advanced settings -> Settings view
    await tester.tap(find.text('Advanced settings'));
    await tester.pumpAndSettle();
    expect(find.text('PERSONALIZE LISAN'), findsOneWidget);
    expect(find.text('Advanced\nsettings'), findsOneWidget);
    expect(find.text('Translate into'), findsOneWidget);
    expect(find.text('Automatic two-way translation'), findsOneWidget);
  });
}
