import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:voicefront/main.dart';

void main() {
  testWidgets('app renders the chat shell', (WidgetTester tester) async {
    await tester.pumpWidget(const VoiceFrontApp());
    await tester.pump();

    expect(find.byType(MaterialApp), findsOneWidget);
    expect(find.textContaining('VoiceFront'), findsWidgets);
  });
}
