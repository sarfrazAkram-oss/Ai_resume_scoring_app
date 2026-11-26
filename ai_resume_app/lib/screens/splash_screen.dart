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
      title: 'Your Career, Smarter.',
      description:
          'Let AI uncover your potential and connect you with opportunities that truly match.',
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
    Navigator.of(context).pushReplacement(
      PageRouteBuilder(
        pageBuilder: (_, __, ___) => const SignInScreen(),
        transitionDuration: Duration.zero,
        reverseTransitionDuration: Duration.zero,
      ),
    );
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
                  for (var index = 0; index < _pages.length; index++)
                    SizedBox(
                      width: pageWidth,
                      child: _OnboardingPage(
                        data: _pages[index],
                        pageWidth: pageWidth,
                        isFirstPage: index == 0,
                        isSecondPage: index == 1,
                        onSkip: _goToSignIn,
                        onNext: () => _scrollToNextPage(context),
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
  const _OnboardingPage({
    required this.data,
    required this.pageWidth,
    required this.isFirstPage,
    required this.isSecondPage,
    required this.onSkip,
    required this.onNext,
  });

  final _OnboardingData data;
  final double pageWidth;
  final bool isFirstPage;
  final bool isSecondPage;
  final VoidCallback onSkip;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    if (isFirstPage) {
      return _FirstOnboardingPage(onSkip: onSkip, onNext: onNext);
    }
    if (isSecondPage) {
      return _SecondOnboardingPage(onSkip: onSkip, onNext: onNext);
    }
    return _ThirdOnboardingPage(onSkip: onSkip, onNext: onNext);
  }
}

class _SecondOnboardingPage extends StatelessWidget {
  const _SecondOnboardingPage({required this.onSkip, required this.onNext});

  final VoidCallback onSkip;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFF0D1422), Color(0xFF111C2C), Color(0xFF101B29)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final wideLayout = constraints.maxWidth >= 900;
            final horizontalPadding = wideLayout ? 40.0 : 24.0;

            return Column(
              children: [
                Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 1360),
                    child: Padding(
                      padding: EdgeInsets.fromLTRB(
                        horizontalPadding,
                        12,
                        horizontalPadding,
                        12,
                      ),
                      child: _FirstPageHeader(onSkip: onSkip),
                    ),
                  ),
                ),
                Expanded(
                  child: wideLayout
                      ? _buildWideContent()
                      : _buildMobileContent(),
                ),
                Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 1360),
                    child: Padding(
                      padding: EdgeInsets.fromLTRB(
                        horizontalPadding,
                        8,
                        horizontalPadding,
                        16,
                      ),
                      child: _SecondPageControls(
                        onNext: onNext,
                        nextSize: wideLayout ? 68 : 66,
                      ),
                    ),
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildWideContent() {
    return LayoutBuilder(
      builder: (context, constraints) {
        final screenWidth = constraints.maxWidth;
        final contentWidth = screenWidth.clamp(0.0, 1360.0);
        final availableHeight = constraints.maxHeight;
        final panelHeight = availableHeight < 520 ? 520.0 : availableHeight;
        final horizontalPadding = screenWidth > 1360 ? 40.0 : 0.0;
        final heroMaxWidth = (contentWidth - horizontalPadding) * 0.55;
        final heroSize = (panelHeight * 0.88)
            .clamp(300.0, heroMaxWidth)
            .clamp(300.0, 650.0)
            .toDouble();

        return SingleChildScrollView(
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: availableHeight),
            child: Center(
              child: SizedBox(
                width: contentWidth,
                height: panelHeight,
                child: Padding(
                  padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
                  child: Row(
                    children: [
                      Expanded(
                        flex: 5,
                        child: Padding(
                          padding: const EdgeInsets.only(right: 48),
                          child: const _SecondPageCopy(desktop: true),
                        ),
                      ),
                      Expanded(
                        flex: 6,
                        child: Center(
                          child: SizedBox.square(
                            dimension: heroSize,
                            child: const _SecondPageHero(),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildMobileContent() {
    return LayoutBuilder(
      builder: (context, constraints) {
        final bodyHeight = constraints.maxHeight;
        final heroSize = (bodyHeight * 0.55)
            .clamp(0.0, constraints.maxWidth - 48)
            .toDouble();

        return SingleChildScrollView(
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: bodyHeight),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    height: heroSize,
                    child: Center(
                      child: SizedBox.square(
                        dimension: heroSize,
                        child: const _SecondPageHero(),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  const _SecondPageCopy(desktop: false),
                  SizedBox(height: bodyHeight > 680 ? 12 : 24),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _SecondPageHero extends StatelessWidget {
  const _SecondPageHero();

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF2679D7).withOpacity(0.18),
            blurRadius: 48,
            spreadRadius: 4,
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(28),
        child: Image.asset(
          'assets/images/ai_candidate_ranking.png',
          fit: BoxFit.contain,
        ),
      ),
    );
  }
}

class _SecondPageCopy extends StatelessWidget {
  const _SecondPageCopy({required this.desktop});

  final bool desktop;

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final titleFontSize = desktop ? 44.0 : (width * 0.083).clamp(30.0, 36.0);
    final descriptionFontSize = desktop
        ? 20.0
        : (width * 0.043).clamp(16.0, 19.0);

    return Column(
      mainAxisAlignment: desktop
          ? MainAxisAlignment.center
          : MainAxisAlignment.start,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        DecoratedBox(
          decoration: BoxDecoration(
            color: const Color(0xFF0F3B4B).withOpacity(0.8),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  Icons.auto_awesome,
                  color: Color(0xFF55DDF4),
                  size: 19,
                ),
                const SizedBox(width: 8),
                Text(
                  'AI-POWERED MATCHING',
                  style: TextStyle(
                    color: const Color(0xFF48D3F0),
                    fontSize: desktop ? 14 : 13,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.2,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 18),
        Text.rich(
          TextSpan(
            style: TextStyle(
              color: const Color(0xFFE6EAF5),
              fontSize: titleFontSize,
              height: 1.1,
              fontWeight: FontWeight.w700,
              letterSpacing: -1.2,
            ),
            children: [
              const TextSpan(text: 'Find the '),
              TextSpan(
                text: 'Perfect Match.',
                style: TextStyle(
                  foreground: Paint()
                    ..shader = const LinearGradient(
                      colors: [
                        Color(0xFF55D7F1),
                        Color(0xFF8CB8FF),
                        Color(0xFFB3A3FF),
                      ],
                    ).createShader(Rect.fromLTWH(0, 0, width, titleFontSize)),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Text(
          'Intelligent scoring and ranking help connect the right talent with the right opportunities.',
          style: TextStyle(
            color: const Color(0xFFD1D9E8),
            fontSize: descriptionFontSize,
            height: 1.65,
            fontWeight: FontWeight.w400,
          ),
        ),
      ],
    );
  }
}

class _SecondPageControls extends StatelessWidget {
  const _SecondPageControls({required this.onNext, required this.nextSize});

  final VoidCallback onNext;
  final double nextSize;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Row(
          children: [
            for (var index = 0; index < 3; index++) ...[
              AnimatedContainer(
                duration: const Duration(milliseconds: 220),
                width: index == 1 ? 50 : 14,
                height: 14,
                decoration: BoxDecoration(
                  color: index == 1 ? null : const Color(0xFF303A49),
                  gradient: index == 1
                      ? const LinearGradient(
                          colors: [Color(0xFF9BC6FF), Color(0xFF48D6F1)],
                        )
                      : null,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: index == 1
                      ? [
                          BoxShadow(
                            color: const Color(0xFF62C9FF).withOpacity(0.38),
                            blurRadius: 12,
                          ),
                        ]
                      : null,
                ),
              ),
              if (index < 2) const SizedBox(width: 14),
            ],
          ],
        ),
        Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: onNext,
            customBorder: const CircleBorder(),
            child: Container(
              width: nextSize,
              height: nextSize,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const LinearGradient(
                  colors: [Color(0xFF55A9FF), Color(0xFF397DE8)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF70A8FF).withOpacity(0.42),
                    blurRadius: 22,
                    spreadRadius: 1,
                  ),
                ],
              ),
              child: Icon(
                Icons.arrow_forward_rounded,
                color: const Color(0xFF07365F),
                size: nextSize * 0.5,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _ThirdOnboardingPage extends StatelessWidget {
  const _ThirdOnboardingPage({required this.onSkip, required this.onNext});

  final VoidCallback onSkip;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFF0D1422), Color(0xFF111C2C), Color(0xFF101B29)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final wideLayout = constraints.maxWidth >= 900;
            final horizontalPadding = wideLayout ? 40.0 : 24.0;
            return Column(
              children: [
                Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 1360),
                    child: Padding(
                      padding: EdgeInsets.fromLTRB(
                        horizontalPadding,
                        12,
                        horizontalPadding,
                        12,
                      ),
                      child: _FirstPageHeader(onSkip: onSkip),
                    ),
                  ),
                ),
                Expanded(
                  child: LayoutBuilder(
                    builder: (context, contentConstraints) {
                      if (wideLayout) {
                        final width = contentConstraints.maxWidth;
                        final availableHeight = contentConstraints.maxHeight;
                        final contentWidth = width.clamp(0.0, 1360.0);
                        final panelHeight = availableHeight < 520
                            ? 520.0
                            : availableHeight;
                        final inset = width > 1360 ? 40.0 : 0.0;
                        final heroLimit = (contentWidth - inset) * 0.55;
                        final heroSize = (panelHeight * 0.88)
                            .clamp(300.0, heroLimit)
                            .clamp(300.0, 650.0)
                            .toDouble();
                        return SingleChildScrollView(
                          child: ConstrainedBox(
                            constraints: BoxConstraints(
                              minHeight: availableHeight,
                            ),
                            child: Center(
                              child: SizedBox(
                                width: contentWidth,
                                height: panelHeight,
                                child: Padding(
                                  padding: EdgeInsets.symmetric(
                                    horizontal: inset,
                                  ),
                                  child: Row(
                                    children: [
                                      const Expanded(
                                        flex: 5,
                                        child: Padding(
                                          padding: EdgeInsets.only(right: 48),
                                          child: _ThirdPageCopy(desktop: true),
                                        ),
                                      ),
                                      Expanded(
                                        flex: 6,
                                        child: Center(
                                          child: SizedBox.square(
                                            dimension: heroSize,
                                            child: const _ThirdPageHero(),
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ),
                          ),
                        );
                      }

                      final availableHeight = contentConstraints.maxHeight;
                      final imageSize = (availableHeight * 0.55)
                          .clamp(0.0, contentConstraints.maxWidth - 48)
                          .toDouble();
                      return SingleChildScrollView(
                        child: ConstrainedBox(
                          constraints: BoxConstraints(
                            minHeight: availableHeight,
                          ),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 24),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                SizedBox(
                                  height: imageSize,
                                  child: Center(
                                    child: SizedBox.square(
                                      dimension: imageSize,
                                      child: const _ThirdPageHero(),
                                    ),
                                  ),
                                ),
                                const SizedBox(height: 20),
                                const _ThirdPageCopy(desktop: false),
                                SizedBox(
                                  height: availableHeight > 680 ? 12 : 24,
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
                Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 1360),
                    child: Padding(
                      padding: EdgeInsets.fromLTRB(
                        horizontalPadding,
                        8,
                        horizontalPadding,
                        16,
                      ),
                      child: _ThirdPageControls(
                        onNext: onNext,
                        wideLayout: wideLayout,
                      ),
                    ),
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _ThirdPageHero extends StatelessWidget {
  const _ThirdPageHero();

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF2679D7).withOpacity(0.18),
            blurRadius: 48,
            spreadRadius: 4,
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(28),
        child: Image.asset(
          'assets/images/ai_interview_hiring.png',
          fit: BoxFit.contain,
        ),
      ),
    );
  }
}

class _ThirdPageCopy extends StatelessWidget {
  const _ThirdPageCopy({required this.desktop});

  final bool desktop;

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final titleSize = desktop ? 44.0 : (width * 0.083).clamp(30.0, 36.0);
    final descriptionSize = desktop ? 20.0 : (width * 0.043).clamp(16.0, 19.0);

    return Column(
      mainAxisAlignment: desktop
          ? MainAxisAlignment.center
          : MainAxisAlignment.start,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        DecoratedBox(
          decoration: BoxDecoration(
            color: const Color(0xFF0F3B4B).withOpacity(0.8),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  Icons.auto_awesome,
                  color: Color(0xFF55DDF4),
                  size: 19,
                ),
                const SizedBox(width: 8),
                Text(
                  'SEAMLESS HIRING EXPERIENCE',
                  style: TextStyle(
                    color: const Color(0xFF48D3F0),
                    fontSize: desktop ? 14 : 12,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.1,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 18),
        Text.rich(
          TextSpan(
            style: TextStyle(
              color: const Color(0xFFE6EAF5),
              fontSize: titleSize,
              height: 1.1,
              fontWeight: FontWeight.w700,
              letterSpacing: -1.2,
            ),
            children: [
              const TextSpan(text: 'From Interview to '),
              TextSpan(
                text: 'Hired.',
                style: TextStyle(
                  foreground: Paint()
                    ..shader = const LinearGradient(
                      colors: [
                        Color(0xFF55D7F1),
                        Color(0xFF8CB8FF),
                        Color(0xFFB3A3FF),
                      ],
                    ).createShader(Rect.fromLTWH(0, 0, width, titleSize)),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Text(
          'Schedule interviews, track candidates, and make confident hiring decisions with automated AI evaluations—all in one place.',
          style: TextStyle(
            color: const Color(0xFFD1D9E8),
            fontSize: descriptionSize,
            height: 1.65,
            fontWeight: FontWeight.w400,
          ),
        ),
      ],
    );
  }
}

class _ThirdPageControls extends StatelessWidget {
  const _ThirdPageControls({required this.onNext, required this.wideLayout});

  final VoidCallback onNext;
  final bool wideLayout;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Row(
          children: [
            for (var index = 0; index < 3; index++) ...[
              AnimatedContainer(
                duration: const Duration(milliseconds: 220),
                width: index == 2 ? 50 : 14,
                height: 14,
                decoration: BoxDecoration(
                  color: index == 2 ? null : const Color(0xFF303A49),
                  gradient: index == 2
                      ? const LinearGradient(
                          colors: [Color(0xFF9BC6FF), Color(0xFF48D6F1)],
                        )
                      : null,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: index == 2
                      ? [
                          BoxShadow(
                            color: const Color(0xFF62C9FF).withOpacity(0.38),
                            blurRadius: 12,
                          ),
                        ]
                      : null,
                ),
              ),
              if (index < 2) const SizedBox(width: 14),
            ],
          ],
        ),
        Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: onNext,
            borderRadius: BorderRadius.circular(48),
            child: Ink(
              padding: EdgeInsets.symmetric(
                horizontal: wideLayout ? 30 : 24,
                vertical: wideLayout ? 20 : 18,
              ),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(48),
                gradient: const LinearGradient(
                  colors: [Color(0xFF4F98FF), Color(0xFF42D5E9)],
                  begin: Alignment.centerLeft,
                  end: Alignment.centerRight,
                ),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF44B9FF).withOpacity(0.35),
                    blurRadius: 28,
                    spreadRadius: 1,
                  ),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'Get Started',
                    style: TextStyle(
                      color: const Color(0xFF07365F),
                      fontSize: wideLayout ? 22 : 20,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Icon(
                    Icons.arrow_forward_rounded,
                    color: const Color(0xFF07365F),
                    size: wideLayout ? 25 : 23,
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _FirstOnboardingPage extends StatelessWidget {
  const _FirstOnboardingPage({required this.onSkip, required this.onNext});

  final VoidCallback onSkip;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFF0D1422), Color(0xFF111C2C), Color(0xFF101B29)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: Stack(
        children: [
          Positioned(
            top: -160,
            right: -140,
            child: IgnorePointer(
              child: Container(
                width: 430,
                height: 430,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(
                    colors: [
                      const Color(0xFF315D9D).withOpacity(0.24),
                      const Color(0xFF315D9D).withOpacity(0),
                    ],
                  ),
                ),
              ),
            ),
          ),
          SafeArea(
            child: LayoutBuilder(
              builder: (context, constraints) {
                final wideLayout = constraints.maxWidth >= 900;
                final horizontalPadding = wideLayout ? 40.0 : 24.0;

                return Column(
                  children: [
                    Center(
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 1360),
                        child: Padding(
                          padding: EdgeInsets.fromLTRB(
                            horizontalPadding,
                            12,
                            horizontalPadding,
                            12,
                          ),
                          child: _FirstPageHeader(onSkip: onSkip),
                        ),
                      ),
                    ),
                    Expanded(
                      child: wideLayout
                          ? _buildWideContent()
                          : _buildMobileContent(),
                    ),
                    Center(
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 1360),
                        child: Padding(
                          padding: EdgeInsets.fromLTRB(
                            horizontalPadding,
                            8,
                            horizontalPadding,
                            16,
                          ),
                          child: _FirstPageControls(
                            onNext: onNext,
                            nextSize: wideLayout ? 68 : 66,
                          ),
                        ),
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWideContent() {
    return LayoutBuilder(
      builder: (context, constraints) {
        final screenWidth = constraints.maxWidth;
        final contentWidth = screenWidth.clamp(0.0, 1360.0);
        final contentHeight = constraints.maxHeight;
        final panelHeight = contentHeight < 520 ? 520.0 : contentHeight;
        final horizontalPadding = screenWidth > 1360 ? 40.0 : 0.0;
        final heroMaxWidth = (contentWidth - horizontalPadding) * 0.52;
        final heroSize = (panelHeight * 0.88)
            .clamp(300.0, heroMaxWidth)
            .clamp(300.0, 600.0)
            .toDouble();

        return SingleChildScrollView(
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: contentHeight),
            child: Center(
              child: SizedBox(
                width: contentWidth,
                height: panelHeight,
                child: Padding(
                  padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
                  child: Row(
                    children: [
                      Expanded(
                        flex: 5,
                        child: Padding(
                          padding: const EdgeInsets.only(right: 48),
                          child: _FirstPageCopy(
                            width: contentWidth * 0.42,
                            desktop: true,
                          ),
                        ),
                      ),
                      Expanded(
                        flex: 6,
                        child: Center(
                          child: SizedBox.square(
                            dimension: heroSize,
                            child: const _FirstPageHero(),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildMobileContent() {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;
        final bodyHeight = constraints.maxHeight;
        final heroSize = (bodyHeight * 0.55).clamp(0.0, width - 48).toDouble();

        return SingleChildScrollView(
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: bodyHeight),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    height: heroSize,
                    child: Center(
                      child: SizedBox.square(
                        dimension: heroSize,
                        child: const _FirstPageHero(),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  _FirstPageCopy(width: width - 48, desktop: false),
                  SizedBox(height: bodyHeight > 680 ? 12 : 24),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _FirstPageHeader extends StatelessWidget {
  const _FirstPageHeader({required this.onSkip});

  final VoidCallback onSkip;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final iconSize = constraints.maxWidth < 360 ? 44.0 : 50.0;

        return Row(
          children: [
            Container(
              width: iconSize,
              height: iconSize,
              decoration: BoxDecoration(
                color: const Color(0xFF293D53),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(
                Icons.hub_rounded,
                color: const Color(0xFF54D7F3),
                size: iconSize * 0.61,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                'AI Resume Ranking',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: const Color(0xFFF3F5FC),
                  fontSize: constraints.maxWidth >= 900 ? 22 : 20,
                  fontWeight: FontWeight.w700,
                  letterSpacing: -0.5,
                ),
              ),
            ),
            const SizedBox(width: 12),
            TextButton(
              onPressed: onSkip,
              style: TextButton.styleFrom(
                foregroundColor: const Color(0xFFE0E7F5),
                backgroundColor: Colors.white.withOpacity(0.07),
                padding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 10,
                ),
                shape: const StadiumBorder(),
                textStyle: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
              child: const Text('Skip'),
            ),
          ],
        );
      },
    );
  }
}

class _FirstPageHero extends StatelessWidget {
  const _FirstPageHero();

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF2679D7).withOpacity(0.18),
            blurRadius: 48,
            spreadRadius: 4,
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(28),
        child: Image.asset(
          'assets/images/resume_ai_scanning.png',
          fit: BoxFit.contain,
        ),
      ),
    );
  }
}

class _FirstPageCopy extends StatelessWidget {
  const _FirstPageCopy({required this.width, required this.desktop});

  final double width;
  final bool desktop;

  @override
  Widget build(BuildContext context) {
    final titleFontSize = desktop ? 46.0 : (width * 0.083).clamp(30.0, 36.0);
    final descriptionFontSize = desktop
        ? 20.0
        : (width * 0.043).clamp(16.0, 19.0);

    return Column(
      mainAxisAlignment: desktop
          ? MainAxisAlignment.center
          : MainAxisAlignment.start,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.auto_awesome, color: Color(0xFF55DDF4), size: 22),
            const SizedBox(width: 10),
            Flexible(
              child: Text(
                'INTELLIGENT RECRUITMENT',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: const Color(0xFF48D3F0),
                  fontSize: desktop ? 15 : 14,
                  fontWeight: FontWeight.w700,
                  letterSpacing: desktop ? 2.0 : 1.6,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Text.rich(
          TextSpan(
            style: TextStyle(
              color: const Color(0xFFE6EAF5),
              fontSize: titleFontSize,
              height: 1.08,
              fontWeight: FontWeight.w700,
              letterSpacing: -1.2,
            ),
            children: [
              const TextSpan(text: 'Your Career, '),
              TextSpan(
                text: 'Smarter.',
                style: TextStyle(
                  foreground: Paint()
                    ..shader = const LinearGradient(
                      colors: [
                        Color(0xFF87C9FF),
                        Color(0xFF5ACAF3),
                        Color(0xFFB3A3FF),
                      ],
                    ).createShader(Rect.fromLTWH(0, 0, width, titleFontSize)),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Text(
          'Let AI uncover your potential and connect you with opportunities that truly match.',
          style: TextStyle(
            color: const Color(0xFFD1D9E8),
            fontSize: descriptionFontSize,
            height: 1.65,
            fontWeight: FontWeight.w400,
          ),
        ),
      ],
    );
  }
}

class _FirstPageControls extends StatelessWidget {
  const _FirstPageControls({required this.onNext, required this.nextSize});

  final VoidCallback onNext;
  final double nextSize;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Row(
          children: [
            Container(
              width: 50,
              height: 14,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF9BC6FF), Color(0xFF48D6F1)],
                ),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF62C9FF).withOpacity(0.38),
                    blurRadius: 12,
                  ),
                ],
              ),
            ),
            const SizedBox(width: 14),
            for (var index = 0; index < 2; index++) ...[
              Container(
                width: 14,
                height: 14,
                decoration: const BoxDecoration(
                  color: Color(0xFF303A49),
                  shape: BoxShape.circle,
                ),
              ),
              if (index == 0) const SizedBox(width: 14),
            ],
          ],
        ),
        Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: onNext,
            customBorder: const CircleBorder(),
            child: Container(
              width: nextSize,
              height: nextSize,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const LinearGradient(
                  colors: [Color(0xFF8CB8FF), Color(0xFF347FE1)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF70A8FF).withOpacity(0.42),
                    blurRadius: 22,
                    spreadRadius: 1,
                  ),
                ],
              ),
              child: Icon(
                Icons.arrow_forward_rounded,
                color: Colors.white,
                size: nextSize * 0.5,
              ),
            ),
          ),
        ),
      ],
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
