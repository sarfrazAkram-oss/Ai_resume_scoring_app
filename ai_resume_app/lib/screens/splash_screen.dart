import 'package:flutter/material.dart';

import 'signin_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  final ScrollController _scrollController = ScrollController();

  static const double _pageWidthFactor = 1.0;
  int _currentPage = 0;

  final List<_OnboardingData> _pages = const [
    _OnboardingData(
      title: 'AI-Based Resume\nScreening & Interview\nSystem',
      description:
          'Automate & enhance your hiring\nprocess with intelligent AI screening & interviews.',
      lightBackground: false,
      variant: _OnboardingVariant.resume,
    ),
    _OnboardingData(
      title: 'Resume Analysis &\nSmart Ranking',
      description:
          'Accurate resume parsing, scoring &\nranking to identify top candidates.',
      lightBackground: true,
      variant: _OnboardingVariant.analysis,
    ),
    _OnboardingData(
      title: 'Adaptive AI-Powered\nInterviews',
      description:
          'Conduct smart interviews with AI-\ngenerated questions tailored to each candidate.',
      lightBackground: true,
      variant: _OnboardingVariant.interview,
    ),
  ];

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _handleScroll() {
    if (!_scrollController.hasClients) {
      return;
    }

    final width = MediaQuery.sizeOf(context).width;
    final pageWidth = width * _pageWidthFactor;
    final currentPage = (_scrollController.offset / pageWidth).round().clamp(
      0,
      _pages.length - 1,
    );

    if (currentPage != _currentPage) {
      setState(() => _currentPage = currentPage);
    }
  }

  void _goToSignIn() {
    Navigator.of(
      context,
    ).pushReplacement(MaterialPageRoute(builder: (_) => const SignInScreen()));
  }

  void _scrollToNextPage(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final pageWidth = width * _pageWidthFactor;
    final currentPage = (_scrollController.offset / pageWidth).round();
    final nextPage = currentPage + 1;

    if (nextPage >= _pages.length) {
      _goToSignIn();
      return;
    }

    _scrollController.animateTo(
      nextPage * pageWidth,
      duration: const Duration(milliseconds: 320),
      curve: Curves.easeOut,
    );
  }

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final pageWidth = width * _pageWidthFactor;

    return Scaffold(
      body: Stack(
        children: [
          SingleChildScrollView(
            controller: _scrollController,
            scrollDirection: Axis.horizontal,
            physics: const BouncingScrollPhysics(),
            child: NotificationListener<ScrollNotification>(
              onNotification: (notification) {
                _handleScroll();
                return false;
              },
              child: Row(
                children: [
                  for (final page in _pages)
                    SizedBox(
                      width: pageWidth,
                      child: _OnboardingPage(data: page, pageWidth: pageWidth),
                    ),
                ],
              ),
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(24, 12, 18, 24),
              child: Column(
                children: [
                  Align(
                    alignment: Alignment.topRight,
                    child: TextButton(
                      onPressed: _goToSignIn,
                      style: TextButton.styleFrom(
                        foregroundColor: const Color(0xFF325C8B),
                        textStyle: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      child: const Text('Skip >'),
                    ),
                  ),
                  const Spacer(),
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Row(
                      children: [
                        const Spacer(),
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: List.generate(_pages.length, (index) {
                            final isActive = index == _currentPage;
                            return AnimatedContainer(
                              duration: const Duration(milliseconds: 220),
                              margin: const EdgeInsets.symmetric(horizontal: 4),
                              width: isActive ? 18 : 7,
                              height: 7,
                              decoration: BoxDecoration(
                                color: isActive
                                    ? const Color(0xFF8FB9E3)
                                    : const Color(0xFFBDD0E6).withOpacity(0.8),
                                borderRadius: BorderRadius.circular(20),
                              ),
                            );
                          }),
                        ),
                        const Spacer(),
                        GestureDetector(
                          onTap: () => _scrollToNextPage(context),
                          child: Container(
                            width: 58,
                            height: 58,
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.72),
                              shape: BoxShape.circle,
                              boxShadow: [
                                BoxShadow(
                                  color: const Color(
                                    0xFF4A79B9,
                                  ).withOpacity(0.08),
                                  blurRadius: 10,
                                  offset: const Offset(0, 6),
                                ),
                              ],
                            ),
                            child: const Icon(
                              Icons.keyboard_arrow_right_rounded,
                              color: Color(0xFF325C8B),
                              size: 36,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _OnboardingPage extends StatelessWidget {
  const _OnboardingPage({required this.data, required this.pageWidth});

  final _OnboardingData data;
  final double pageWidth;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: pageWidth,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF1C4678), Color(0xFF2E5C93)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            children: [
              const SizedBox(height: 12),
              Expanded(
                child: Column(
                  children: [
                    Expanded(
                      flex: 56,
                      child: Center(
                        child: _OnboardingArtwork(
                          variant: data.variant,
                          lightBackground: data.lightBackground,
                        ),
                      ),
                    ),
                    Expanded(
                      flex: 44,
                      child: Padding(
                        padding: const EdgeInsets.only(top: 6),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.start,
                          children: [
                            Text(
                              data.title,
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 28,
                                height: 1.18,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                            const SizedBox(height: 18),
                            Text(
                              data.description,
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                color: Colors.white.withOpacity(0.88),
                                fontSize: 16,
                                height: 1.55,
                                fontWeight: FontWeight.w400,
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
        ),
      ),
    );
  }
}

class _OnboardingData {
  const _OnboardingData({
    required this.title,
    required this.description,
    required this.lightBackground,
    required this.variant,
  });

  final String title;
  final String description;
  final bool lightBackground;
  final _OnboardingVariant variant;
}

enum _OnboardingVariant { resume, analysis, interview }

class _OnboardingArtwork extends StatelessWidget {
  const _OnboardingArtwork({
    required this.variant,
    required this.lightBackground,
  });

  final _OnboardingVariant variant;
  final bool lightBackground;

  @override
  Widget build(BuildContext context) {
    switch (variant) {
      case _OnboardingVariant.resume:
        return _HeroCanvas(
          dark: true,
          child: Stack(
            alignment: Alignment.center,
            children: [
              Positioned.fill(
                child: IgnorePointer(
                  child: CustomPaint(painter: _TechBackdropPainter(dark: true)),
                ),
              ),
              Positioned(
                left: 18,
                top: 60,
                child: _FloatingCard(
                  width: 102,
                  height: 152,
                  color: const Color(0xFF2A5A98).withOpacity(0.75),
                ),
              ),
              Positioned(right: 18, top: 54, child: _ResumePanel(dark: true)),
              Positioned(
                left: 16,
                bottom: 20,
                child: _AbstractTechCore(dark: true, scale: 1.05),
              ),
              Positioned(
                right: 34,
                bottom: 26,
                child: _ClipboardCard(dark: true),
              ),
            ],
          ),
        );
      case _OnboardingVariant.analysis:
        return _HeroCanvas(
          dark: false,
          child: Stack(
            alignment: Alignment.center,
            children: [
              Positioned.fill(
                child: IgnorePointer(
                  child: CustomPaint(
                    painter: _TechBackdropPainter(dark: false),
                  ),
                ),
              ),
              Positioned(
                left: 8,
                top: 40,
                child: _FloatingCard(
                  width: 82,
                  height: 186,
                  color: const Color(0xFFF5FAFF),
                ),
              ),
              Positioned(
                top: 18,
                left: 72,
                right: 72,
                child: _ClipboardCard(dark: false),
              ),
              Positioned(right: 10, top: 94, child: _GrowthGraph()),
              Positioned(
                right: 24,
                bottom: 8,
                child: _AbstractTechCore(dark: false, scale: 0.82),
              ),
            ],
          ),
        );
      case _OnboardingVariant.interview:
        return _HeroCanvas(
          dark: false,
          child: Stack(
            alignment: Alignment.center,
            children: [
              Positioned.fill(
                child: IgnorePointer(
                  child: CustomPaint(
                    painter: _TechBackdropPainter(dark: false),
                  ),
                ),
              ),
              Positioned(
                left: 20,
                top: 34,
                child: _AbstractTechCore(dark: false, scale: 0.72),
              ),
              Positioned(
                right: 30,
                top: 44,
                child: _InterviewBubble(
                  label: 'AI Interview Question',
                  dark: true,
                ),
              ),
              Positioned(right: 22, bottom: 24, child: _CandidateCard()),
              Positioned(
                left: 22,
                bottom: 22,
                child: _AbstractTechCore(dark: false, scale: 0.58),
              ),
            ],
          ),
        );
    }
  }
}

class _HeroCanvas extends StatelessWidget {
  const _HeroCanvas({required this.child, required this.dark});

  final Widget child;
  final bool dark;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 320,
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: dark
              ? const LinearGradient(
                  colors: [Color(0xFF123A69), Color(0xFF2A5A98)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                )
              : const LinearGradient(
                  colors: [Color(0xFFF7FAFF), Color(0xFFECF3FF)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
          borderRadius: BorderRadius.circular(28),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF4A79B9).withOpacity(dark ? 0.28 : 0.12),
              blurRadius: 30,
              offset: const Offset(0, 14),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(28),
          child: Stack(
            children: [
              Positioned.fill(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: RadialGradient(
                      center: const Alignment(-0.2, -0.7),
                      radius: 1.2,
                      colors: [
                        dark
                            ? Colors.white.withOpacity(0.08)
                            : Colors.white.withOpacity(0.55),
                        Colors.transparent,
                      ],
                    ),
                  ),
                ),
              ),
              if (dark)
                Positioned.fill(
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: RadialGradient(
                        center: const Alignment(-0.45, -0.6),
                        radius: 1.1,
                        colors: [
                          Colors.white.withOpacity(0.16),
                          Colors.transparent,
                        ],
                      ),
                    ),
                  ),
                ),
              Positioned.fill(child: child),
            ],
          ),
        ),
      ),
    );
  }
}

class _AbstractTechCore extends StatelessWidget {
  const _AbstractTechCore({required this.dark, required this.scale});

  final bool dark;
  final double scale;

  @override
  Widget build(BuildContext context) {
    final outerColor = dark ? const Color(0xFFF2F7FF) : const Color(0xFFF8FBFF);
    final innerColor = dark ? const Color(0xFF1E4F87) : const Color(0xFF5A97E7);
    final accent = dark ? const Color(0xFF5DB2FF) : const Color(0xFF89B9E9);

    return Transform.scale(
      scale: scale,
      child: SizedBox(
        width: 176,
        height: 176,
        child: Stack(
          alignment: Alignment.center,
          children: [
            Container(
              width: 150,
              height: 150,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    outerColor.withOpacity(dark ? 0.95 : 0.88),
                    outerColor.withOpacity(dark ? 0.25 : 0.14),
                  ],
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(dark ? 0.12 : 0.06),
                    blurRadius: 22,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
            ),
            Container(
              width: 112,
              height: 112,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: innerColor.withOpacity(dark ? 0.85 : 0.14),
                border: Border.all(
                  color: innerColor.withOpacity(dark ? 0.55 : 0.25),
                  width: 5,
                ),
              ),
            ),
            Positioned(
              top: 24,
              left: 20,
              child: _TechChip(color: accent, width: 20, height: 20),
            ),
            Positioned(
              top: 20,
              right: 18,
              child: _TechChip(
                color: accent.withOpacity(0.85),
                width: 14,
                height: 14,
              ),
            ),
            Positioned(
              bottom: 18,
              left: 26,
              child: _TechChip(
                color: innerColor.withOpacity(0.9),
                width: 26,
                height: 10,
              ),
            ),
            Positioned(
              bottom: 18,
              right: 26,
              child: _TechChip(
                color: innerColor.withOpacity(0.9),
                width: 26,
                height: 10,
              ),
            ),
            Container(
              width: 88,
              height: 88,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: dark ? const Color(0xFFF4F8FF) : Colors.white,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(dark ? 0.14 : 0.07),
                    blurRadius: 18,
                    offset: const Offset(0, 8),
                  ),
                ],
              ),
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Container(
                    width: 46,
                    height: 46,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: RadialGradient(
                        colors: [
                          accent.withOpacity(0.95),
                          innerColor.withOpacity(0.95),
                        ],
                      ),
                    ),
                  ),
                  Container(
                    width: 16,
                    height: 16,
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.96),
                      shape: BoxShape.circle,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TechChip extends StatelessWidget {
  const _TechChip({
    required this.color,
    required this.width,
    required this.height,
  });

  final Color color;
  final double width;
  final double height;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(999),
      ),
    );
  }
}

class _TechBackdropPainter extends CustomPainter {
  _TechBackdropPainter({required this.dark});

  final bool dark;

  @override
  void paint(Canvas canvas, Size size) {
    final dotPaint = Paint()
      ..color = (dark ? Colors.white : const Color(0xFFBFD3EA)).withOpacity(
        dark ? 0.12 : 0.3,
      )
      ..style = PaintingStyle.fill;

    final ringPaint = Paint()
      ..color = (dark ? Colors.white : const Color(0xFF7FB2E2)).withOpacity(
        dark ? 0.08 : 0.14,
      )
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2;

    for (var index = 0; index < 10; index++) {
      final x = (size.width * 0.12) + (index * size.width * 0.08) % size.width;
      final y =
          (index.isEven ? size.height * 0.18 : size.height * 0.7) +
          (index * 11) % 30;
      canvas.drawCircle(Offset(x, y), index.isEven ? 2.2 : 1.6, dotPaint);
    }

    canvas.drawCircle(
      Offset(size.width * 0.24, size.height * 0.22),
      34,
      ringPaint,
    );
    canvas.drawCircle(
      Offset(size.width * 0.76, size.height * 0.26),
      28,
      ringPaint,
    );
    canvas.drawCircle(
      Offset(size.width * 0.82, size.height * 0.72),
      40,
      ringPaint,
    );

    final linePaint = Paint()
      ..color = (dark ? Colors.white : const Color(0xFF95B7D8)).withOpacity(
        dark ? 0.08 : 0.16,
      )
      ..strokeWidth = 1;

    canvas.drawLine(
      Offset(size.width * 0.12, size.height * 0.52),
      Offset(size.width * 0.44, size.height * 0.52),
      linePaint,
    );
    canvas.drawLine(
      Offset(size.width * 0.58, size.height * 0.58),
      Offset(size.width * 0.88, size.height * 0.42),
      linePaint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _FloatingCard extends StatelessWidget {
  const _FloatingCard({
    required this.width,
    required this.height,
    required this.color,
  });

  final double width;
  final double height;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(18),
      ),
    );
  }
}

class _ResumePanel extends StatelessWidget {
  const _ResumePanel({required this.dark});

  final bool dark;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 122,
      height: 170,
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: dark ? Colors.white.withOpacity(0.92) : Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 16,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: const Color(0xFFDAE9FF),
              borderRadius: BorderRadius.circular(10),
            ),
          ),
          const SizedBox(height: 10),
          Container(
            width: 58,
            height: 7,
            decoration: BoxDecoration(
              color: const Color(0xFFB3CAE7),
              borderRadius: BorderRadius.circular(10),
            ),
          ),
          const SizedBox(height: 10),
          Container(
            width: 84,
            height: 8,
            decoration: BoxDecoration(
              color: const Color(0xFFE0EAF7),
              borderRadius: BorderRadius.circular(10),
            ),
          ),
          const SizedBox(height: 8),
          Container(
            width: 70,
            height: 8,
            decoration: BoxDecoration(
              color: const Color(0xFFEEF3FA),
              borderRadius: BorderRadius.circular(10),
            ),
          ),
          const Spacer(),
          Container(
            width: 66,
            height: 8,
            decoration: BoxDecoration(
              color: const Color(0xFFBFD3ED),
              borderRadius: BorderRadius.circular(10),
            ),
          ),
        ],
      ),
    );
  }
}

class _ClipboardCard extends StatelessWidget {
  const _ClipboardCard({required this.dark});

  final bool dark;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 110,
      height: 146,
      padding: const EdgeInsets.all(9),
      decoration: BoxDecoration(
        color: dark ? Colors.white.withOpacity(0.93) : Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 14,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        children: [
          Container(
            width: 24,
            height: 8,
            decoration: BoxDecoration(
              color: const Color(0xFF9FB9D8),
              borderRadius: BorderRadius.circular(10),
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: const Color(0xFFF3F8FF),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Column(
                children: [
                  const SizedBox(height: 10),
                  Container(
                    width: 62,
                    height: 6,
                    decoration: BoxDecoration(
                      color: const Color(0xFFD0DEF0),
                      borderRadius: BorderRadius.circular(20),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    width: 48,
                    height: 6,
                    decoration: BoxDecoration(
                      color: const Color(0xFFE2EBF7),
                      borderRadius: BorderRadius.circular(20),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    width: 72,
                    height: 6,
                    decoration: BoxDecoration(
                      color: const Color(0xFFC4D9F3),
                      borderRadius: BorderRadius.circular(20),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Container(
                    width: 48,
                    height: 6,
                    decoration: BoxDecoration(
                      color: const Color(0xFFE2EBF7),
                      borderRadius: BorderRadius.circular(20),
                    ),
                  ),
                  const Spacer(),
                  Container(
                    width: 68,
                    height: 8,
                    margin: const EdgeInsets.only(bottom: 8),
                    decoration: BoxDecoration(
                      color: const Color(0xFFB6CBE6),
                      borderRadius: BorderRadius.circular(20),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _GrowthGraph extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 88,
      height: 120,
      child: Stack(
        children: [
          Positioned(
            bottom: 0,
            left: 8,
            child: Container(
              width: 14,
              height: 56,
              decoration: BoxDecoration(
                color: const Color(0xFF89B9E9),
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
          Positioned(
            bottom: 0,
            left: 30,
            child: Container(
              width: 14,
              height: 82,
              decoration: BoxDecoration(
                color: const Color(0xFF5D98E1),
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
          Positioned(
            bottom: 0,
            right: 18,
            child: Container(
              width: 14,
              height: 100,
              decoration: BoxDecoration(
                color: const Color(0xFF2F68C0),
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
          Positioned(
            right: 6,
            top: 2,
            child: Transform.rotate(
              angle: -0.7,
              child: Icon(
                Icons.trending_up_rounded,
                color: const Color(0xFF2D67C1),
                size: 38,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _InterviewBubble extends StatelessWidget {
  const _InterviewBubble({required this.label, required this.dark});

  final String label;
  final bool dark;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
      decoration: BoxDecoration(
        color: dark ? const Color(0xFF3A7BD7) : Colors.white,
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 12,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Text(
        label,
        style: TextStyle(
          color: dark ? Colors.white : const Color(0xFF325C8B),
          fontWeight: FontWeight.w700,
          fontSize: 12,
        ),
      ),
    );
  }
}

class _CandidateCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      width: 122,
      height: 74,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 12,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 76,
            height: 8,
            decoration: BoxDecoration(
              color: const Color(0xFFD7E2F0),
              borderRadius: BorderRadius.circular(20),
            ),
          ),
          const SizedBox(height: 8),
          Container(
            width: 54,
            height: 8,
            decoration: BoxDecoration(
              color: const Color(0xFFE7EEF7),
              borderRadius: BorderRadius.circular(20),
            ),
          ),
          const Spacer(),
          Container(
            width: 28,
            height: 8,
            decoration: BoxDecoration(
              color: const Color(0xFFB7CBE4),
              borderRadius: BorderRadius.circular(20),
            ),
          ),
        ],
      ),
    );
  }
}
