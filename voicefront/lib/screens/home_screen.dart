import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../data/static_data.dart';
import '../widgets/category_card.dart';
import '../widgets/recent_storefront_card.dart';
import '../widgets/pill_button.dart';

class HomeScreen extends StatelessWidget {
  final VoidCallback onNavigateToRecord;
  final VoidCallback onNavigateToStorefronts;

  const HomeScreen({
    super.key,
    required this.onNavigateToRecord,
    required this.onNavigateToStorefronts,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: const Padding(
          padding: EdgeInsets.all(14),
          child: Icon(Icons.translate, color: AppColors.brandBlue, size: 24),
        ),
        title: const Text('VoiceFront'),
        actions: [
          Stack(
            children: [
              const Padding(
                padding: EdgeInsets.all(14),
                child: Icon(Icons.notifications_outlined, size: 24),
              ),
              Positioned(
                right: 10,
                top: 10,
                child: Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                    color: AppColors.error,
                    shape: BoxShape.circle,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeroSection(context),
            const SizedBox(height: 28),
            _buildCategoriesSection(),
            const SizedBox(height: 28),
            _buildRecentSection(context),
            const SizedBox(height: 100),
          ],
        ),
      ),
    );
  }

  Widget _buildHeroSection(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppColors.brandBlue.withValues(alpha: 0.05),
            AppColors.mintGreen.withValues(alpha: 0.12),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Create your online store\nwith just your voice',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
              height: 1.3,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'अपनी आवाज़ से अपना ऑनलाइन स्टोर बनाएं',
            style: TextStyle(
              fontSize: 13,
              color: AppColors.textSecondary.withValues(alpha: 0.8),
            ),
          ),
          const SizedBox(height: 20),
          PillButton(
            text: 'Start Recording / रिकॉर्डिंग शुरू करें',
            icon: Icons.mic_rounded,
            onPressed: onNavigateToRecord,
          ),
        ],
      ),
    );
  }

  Widget _buildCategoriesSection() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Categories / श्रेणियां',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 14),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: 1.3,
            ),
            itemCount: categories.length,
            itemBuilder: (context, index) {
              return CategoryCard(category: categories[index]);
            },
          ),
        ],
      ),
    );
  }

  Widget _buildRecentSection(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Recently Created Storefronts',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'हाल ही में बनाए गए स्टोर',
                    style: TextStyle(
                      fontSize: 12,
                      color: AppColors.textSecondary.withValues(alpha: 0.7),
                    ),
                  ),
                ],
              ),
              TextButton(
                onPressed: onNavigateToStorefronts,
                child: const Text(
                  'View All',
                  style: TextStyle(
                    color: AppColors.brandBlue,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 230,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: recentStorefronts.length,
              itemBuilder: (context, index) {
                return RecentStorefrontCard(
                  storefront: recentStorefronts[index],
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
