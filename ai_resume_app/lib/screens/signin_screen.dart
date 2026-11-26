import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../widgets/custom_button.dart';
import '../widgets/custom_textfield.dart';
import 'home_screen.dart';
import 'recruiter_dashboard_screen.dart';
import 'signup_screen.dart';

const String _authorizedHrEmail = 'meharsarfaraz206905@gmail.com';

class SignInScreen extends StatefulWidget {
  const SignInScreen({super.key});

  @override
  State<SignInScreen> createState() => _SignInScreenState();
}

class _SignInScreenState extends State<SignInScreen> {
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  bool _obscurePassword = true;
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn.instance;
  bool _googleInitialized = false;

  @override
  void initState() {
    super.initState();
    _initializeGoogleSignIn();
  }

  Future<void> _initializeGoogleSignIn() async {
    if (_googleInitialized) return;
    try {
      await _googleSignIn.initialize();
      _googleInitialized = true;
    } catch (_) {
      _googleInitialized = true;
    }
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _handlePasswordReset() async {
    final emailController = TextEditingController(
      text: _usernameController.text.trim(),
    );
    final email = await showDialog<String>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Reset Password'),
          content: TextField(
            controller: emailController,
            keyboardType: TextInputType.emailAddress,
            autofocus: true,
            decoration: const InputDecoration(labelText: 'Email'),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () =>
                  Navigator.of(dialogContext).pop(emailController.text.trim()),
              child: const Text('Send Reset Email'),
            ),
          ],
        );
      },
    );
    emailController.dispose();

    if (email == null) {
      return;
    }
    if (email.isEmpty) {
      _showMessage('Please enter your registered email address.');
      return;
    }

    try {
      await FirebaseAuth.instance.sendPasswordResetEmail(email: email);
      _showMessage(
        'Password reset email has been sent. Please check your email and set a new password.',
      );
    } on FirebaseAuthException catch (e) {
      if (e.code == 'invalid-email') {
        _showMessage('Please enter a valid email address.');
      } else if (e.code == 'user-not-found') {
        _showMessage('No account was found for that email address.');
      } else {
        _showMessage(e.message ?? 'Could not send the password reset email.');
      }
    } catch (_) {
      _showMessage(
        'Could not send the password reset email. Please try again.',
      );
    }
  }

  Future<void> _navigateToHome() async {
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) =>
            const HomeScreen(),
        transitionDuration: Duration.zero,
        reverseTransitionDuration: Duration.zero,
      ),
    );
  }

  Future<void> _navigateToRecruiterDashboard() async {
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) =>
            const RecruiterDashboardScreen(),
        transitionDuration: Duration.zero,
        reverseTransitionDuration: Duration.zero,
      ),
    );
  }

  Future<void> _handleLogin() async {
    final email = _usernameController.text.trim();
    final password = _passwordController.text;

    if (email.isEmpty || password.isEmpty) {
      _showMessage('Please enter both email and password.');
      return;
    }

    try {
      final credential = await _auth.signInWithEmailAndPassword(
        email: email,
        password: password,
      );

      final signedInEmail = credential.user?.email?.toLowerCase();
      if (signedInEmail == _authorizedHrEmail) {
        await _navigateToRecruiterDashboard();
        return;
      }

      await _navigateToHome();
    } on FirebaseAuthException catch (e) {
      if (e.code == 'user-not-found') {
        _showMessage('No user found for that email.');
      } else if (e.code == 'wrong-password') {
        _showMessage('Incorrect password.');
      } else {
        _showMessage(e.message ?? 'Login failed. Please try again.');
      }
    } catch (e) {
      _showMessage('Login failed. Please check your connection and try again.');
    }
  }

  Future<void> _handleCandidateLogin() async {
    final email = _usernameController.text.trim();
    final password = _passwordController.text;

    if (email.isEmpty || password.isEmpty) {
      _showMessage('Please enter both email and password.');
      return;
    }

    try {
      await _auth.signInWithEmailAndPassword(email: email, password: password);
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) {
        _showMessage('Candidate login failed. Please try again.');
        return;
      }

      debugPrint('Candidate login successful');
      debugPrint('Candidate auth uid: ${user.uid}');
      debugPrint('Candidate auth email: ${user.email}');
      await _navigateToHome();
    } on FirebaseAuthException catch (e) {
      if (e.code == 'user-not-found') {
        _showMessage('No user found for that email.');
      } else if (e.code == 'wrong-password') {
        _showMessage('Incorrect password.');
      } else {
        _showMessage(e.message ?? 'Login failed. Please try again.');
      }
    } catch (_) {
      _showMessage('Login failed. Please check your connection and try again.');
    }
  }

  Future<void> _attemptRecruiterAccess() async {
    final user = _auth.currentUser;
    if (user != null && user.email?.toLowerCase() == _authorizedHrEmail) {
      await _navigateToRecruiterDashboard();
      return;
    }

    _showMessage(
      'Please sign in with the authorized HR email and password to access the recruiter dashboard.',
    );
  }

  Future<void> _handleGoogleSignIn() async {
    try {
      final googleUser = await _googleSignIn.authenticate();
      final googleAuth = googleUser.authentication;
      final credential = GoogleAuthProvider.credential(
        idToken: googleAuth.idToken,
      );

      final userCredential = await _auth.signInWithCredential(credential);
      final signedInEmail = userCredential.user?.email?.toLowerCase();
      if (signedInEmail == _authorizedHrEmail) {
        await _auth.signOut();
        await _googleSignIn.signOut();
        _showMessage(
          'Google sign-in is not authorized for HR access. Please use email and password.',
        );
        return;
      }

      await _navigateToHome();
    } on FirebaseAuthException catch (e) {
      _showMessage(e.message ?? 'Google sign-in failed.');
    } catch (_) {
      _showMessage('Google sign-in failed. Please try again.');
    }
  }

  void _goToSignUp() {
    Navigator.of(context).push(
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) =>
            const SignUpScreen(),
        transitionDuration: Duration.zero,
        reverseTransitionDuration: Duration.zero,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFF7FAFF), Color(0xFFF0F5FD)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                children: [
                  const SizedBox(height: 14),
                  const SizedBox(height: 2),
                  SizedBox(
                    height: 180,
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        Container(
                          width: 154,
                          height: 154,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: RadialGradient(
                              colors: [
                                const Color(0xFF6CA8F0).withValues(alpha: 0.85),
                                const Color(0xFFCADCF3).withValues(alpha: 0.18),
                                Colors.transparent,
                              ],
                              stops: const [0.0, 0.7, 1.0],
                            ),
                          ),
                        ),
                        Positioned(top: 8, child: _LoginRobotArt()),
                      ],
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Log In',
                    style: TextStyle(
                      fontSize: 30,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFF325C8B),
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Welcome back!',
                    style: TextStyle(fontSize: 16, color: Color(0xFF61748D)),
                  ),
                  const SizedBox(height: 26),
                  CustomTextField(
                    controller: _usernameController,
                    hintText: 'Enter your username',
                    icon: Icons.person_rounded,
                    textInputAction: TextInputAction.next,
                  ),
                  const SizedBox(height: 12),
                  CustomTextField(
                    controller: _passwordController,
                    hintText: 'Enter your password',
                    icon: Icons.lock_rounded,
                    obscureText: _obscurePassword,
                    suffixIcon: Icon(
                      _obscurePassword
                          ? Icons.visibility_off_rounded
                          : Icons.visibility_rounded,
                      color: const Color(0xFF9FB2C8),
                    ),
                    onSuffixTap: () {
                      setState(() {
                        _obscurePassword = !_obscurePassword;
                      });
                    },
                  ),
                  const SizedBox(height: 12),
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton(
                      onPressed: _handlePasswordReset,
                      style: TextButton.styleFrom(
                        foregroundColor: const Color(0xFF5A7FA9),
                        padding: EdgeInsets.zero,
                      ),
                      child: const Text('Forgot Password?'),
                    ),
                  ),
                  const SizedBox(height: 4),
                  CustomButton(
                    text: 'Log In',
                    onPressed: _handleLogin,
                    height: 54,
                  ),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text(
                        "Don't have an account? ",
                        style: TextStyle(
                          color: Color(0xFF5F7088),
                          fontSize: 15,
                        ),
                      ),
                      GestureDetector(
                        onTap: _goToSignUp,
                        child: const Text(
                          'Sign Up',
                          style: TextStyle(
                            color: Color(0xFF2C72D2),
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 18),
                  Row(
                    children: const [
                      Expanded(child: Divider(color: Color(0xFFD5DEEA))),
                      Padding(
                        padding: EdgeInsets.symmetric(horizontal: 12),
                        child: Text(
                          'Or Log In with',
                          style: TextStyle(
                            color: Color(0xFF7B8CA4),
                            fontSize: 14,
                          ),
                        ),
                      ),
                      Expanded(child: Divider(color: Color(0xFFD5DEEA))),
                    ],
                  ),
                  const SizedBox(height: 14),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      _SocialButton(
                        label: 'G',
                        labelStyle: const TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w800,
                          color: Color(0xFF4285F4),
                        ),
                        onTap: _handleGoogleSignIn,
                      ),
                    ],
                  ),
                  const SizedBox(height: 18),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _LoginRobotArt extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      width: 140,
      height: 140,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Colors.white.withValues(alpha: 0.2),
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          Container(
            width: 124,
            height: 124,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: const Color(0xFFF4F8FF).withValues(alpha: 0.98),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.08),
                  blurRadius: 18,
                  offset: const Offset(0, 10),
                ),
              ],
            ),
            child: Stack(
              children: [
                Positioned(
                  left: 12,
                  top: 18,
                  child: Container(
                    width: 28,
                    height: 28,
                    decoration: BoxDecoration(
                      color: const Color(0xFFD9E8FA),
                      shape: BoxShape.circle,
                    ),
                    child: Center(
                      child: Container(
                        width: 12,
                        height: 12,
                        decoration: BoxDecoration(
                          color: const Color(0xFF5A97E7),
                          shape: BoxShape.circle,
                        ),
                      ),
                    ),
                  ),
                ),
                Positioned(
                  right: 12,
                  top: 18,
                  child: Container(
                    width: 28,
                    height: 28,
                    decoration: BoxDecoration(
                      color: const Color(0xFFD9E8FA),
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
                Center(
                  child: Container(
                    width: 82,
                    height: 56,
                    decoration: BoxDecoration(
                      color: const Color(0xFF1E4F87),
                      borderRadius: BorderRadius.circular(30),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
                          width: 16,
                          height: 16,
                          decoration: const BoxDecoration(
                            color: Color(0xFF5DB2FF),
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Container(
                          width: 16,
                          height: 16,
                          decoration: const BoxDecoration(
                            color: Color(0xFF5DB2FF),
                            shape: BoxShape.circle,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SocialButton extends StatelessWidget {
  const _SocialButton({
    required this.label,
    required this.labelStyle,
    this.onTap,
  });

  final String label;
  final TextStyle labelStyle;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 66,
        height: 42,
        margin: const EdgeInsets.symmetric(horizontal: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFFDCE5F1)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.04),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        alignment: Alignment.center,
        child: Text(label, style: labelStyle),
      ),
    );
  }
}
