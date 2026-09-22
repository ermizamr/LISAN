// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ethiopian_translator/main.dart';

void main() {
  testWidgets('translator shell renders and records a turn', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const TranslatorApp());

    expect(find.text('Lisan'), findsOneWidget);
    expect(find.text('Tap to speak'), findsOneWidget);

    await tester.tap(find.byIcon(Icons.mic_rounded));
    await tester.pump();
    expect(find.text('Listening...'), findsOneWidget);

    await tester.tap(find.byIcon(Icons.stop_rounded));
    await tester.pumpAndSettle();
    expect(find.text('I need help, please.'), findsOneWidget);
  });
}
