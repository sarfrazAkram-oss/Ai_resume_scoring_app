// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_core_platform_interface/test.dart';
import 'package:ai_resume_app/main.dart';
import 'package:ai_resume_app/screens/home_screen.dart';
import 'package:ai_resume_app/screens/signin_screen.dart';
import 'package:ai_resume_app/screens/signup_screen.dart';
import 'package:ai_resume_app/widgets/custom_button.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    TestFirebaseCoreHostApi.setUp(MockFirebaseApp());
    await Firebase.initializeApp();
  });

  testWidgets('App boots into splash screen', (WidgetTester tester) async {
    await tester.pumpWidget(const AiResumeApp());

    expect(find.text('Skip'), findsNWidgets(3));
    expect(find.text('Your Career, Smarter.'), findsOneWidget);
  });

  testWidgets('Current home screen lays out on narrow widths', (
    WidgetTester tester,
  ) async {
    tester.view.physicalSize = const Size(320, 800);
    tester.view.devicePixelRatio = 1.0;

    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const MaterialApp(home: HomeScreen()));

    expect(find.text('Available Jobs'), findsOneWidget);
    expect(find.text('My Applications'), findsOneWidget);
  });

  testWidgets('Login form validates missing credentials', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const MaterialApp(home: SignInScreen()));

    final loginButton = find.byWidgetPredicate(
      (widget) => widget is CustomButton && widget.text == 'Log In',
    );

    await tester.ensureVisible(loginButton);
    await tester.tap(loginButton);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.text('Please enter both email and password.'), findsOneWidget);
    expect(find.byType(SignInScreen), findsOneWidget);
  });

  testWidgets('Signup form validates missing required fields', (
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

    await tester.ensureVisible(signUpButton);
    await tester.tap(signUpButton);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.text('Please complete all required fields.'), findsOneWidget);
    expect(find.byType(SignUpScreen), findsOneWidget);
  });
}
