// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ai_resume_app/main.dart';
import 'package:ai_resume_app/screens/home_screen.dart';
import 'package:ai_resume_app/widgets/custom_button.dart';
import 'package:ai_resume_app/screens/signin_screen.dart';
import 'package:ai_resume_app/screens/signup_screen.dart';

void main() {
  testWidgets('App boots into splash screen', (WidgetTester tester) async {
    await tester.pumpWidget(const AiResumeApp());

    expect(find.text('Skip >'), findsOneWidget);
    expect(find.text('AI-Based Resume'), findsNothing);
  });

  testWidgets('Home screen lays out on narrow widths', (
    WidgetTester tester,
  ) async {
    tester.view.physicalSize = const Size(320, 800);
    tester.view.devicePixelRatio = 1.0;

    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const MaterialApp(home: HomeScreen()));

    expect(find.text('Analyze Resume'), findsOneWidget);
    expect(find.text('Resume History'), findsOneWidget);
  });

  testWidgets('Login button navigates to visible home screen', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const MaterialApp(home: SignInScreen()));

    final loginButton = find.byWidgetPredicate(
      (widget) => widget is CustomButton && widget.text == 'Log In',
    );

    await tester.tap(loginButton);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Resume Score'), findsOneWidget);
    expect(find.text('Main Menu'), findsOneWidget);
  });

  testWidgets('Signup button navigates to visible home screen', (
    WidgetTester tester,
  ) async {
    tester.view.physicalSize = const Size(800, 1400);
    tester.view.devicePixelRatio = 1.0;

    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const MaterialApp(home: SignUpScreen()));

    final signUpButton = find.byWidgetPredicate(
      (widget) => widget is CustomButton && widget.text == 'Sign Up',
    );

    await tester.tap(signUpButton);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Resume Score'), findsOneWidget);
    expect(find.text('Main Menu'), findsOneWidget);
  });
}
