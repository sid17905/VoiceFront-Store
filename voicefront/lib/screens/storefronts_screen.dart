import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../data/static_data.dart';

class StorefrontsScreen extends StatelessWidget {
  final VoidCallback onNewStore;

  const StorefrontsScreen({super.key, required this.onNewStore});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(),
            const SizedBox(height: 16),
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: storefrontList.length,
                itemBuilder: (context, index) {
                  return _buildStoreCard(storefrontList[index]);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Your Stores / आपके स्टोर',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Manage and track your voice-built storefronts.',
                  style: TextStyle(
                    fontSize: 13,
                    color: AppColors.textSecondary.withValues(alpha: 0.8),
                  ),
                ),
              ],
            ),
          ),
          Container(
            decoration: BoxDecoration(
              color: AppColors.brandBlue,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: onNewStore,
                borderRadius: BorderRadius.circular(20),
                child: const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.add, color: AppColors.white, size: 16),
                      SizedBox(width: 4),
                      Text(
                        'New Store',
                        style: TextStyle(
                          color: AppColors.white,
                          fontWeight: FontWeight.w600,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStoreCard(StorefrontListItem store) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildStoreHeader(store),
          const SizedBox(height: 12),
          if (store.liveUrl != null) _buildLiveUrl(store),
          if (store.actionText != null) _buildActionText(store),
          if (store.progress != null) _buildProgressInfo(store),
          const SizedBox(height: 12),
          _buildStoreButtons(store),
        ],
      ),
    );
  }

  Widget _buildStoreHeader(StorefrontListItem store) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: AppColors.cardBg,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Text(store.icon, style: const TextStyle(fontSize: 24)),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                store.name,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 4),
              Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: Color(store.statusColorValue),
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    store.status,
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: Color(store.statusColorValue),
                      letterSpacing: 0.5,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        Container(
          padding: const EdgeInsets.all(6),
          decoration: BoxDecoration(
            color: AppColors.cardBg,
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Icon(
            Icons.edit_outlined,
            size: 18,
            color: AppColors.textSecondary,
          ),
        ),
      ],
    );
  }

  Widget _buildLiveUrl(StorefrontListItem store) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          const Text(
            'Quality Assurance: ',
            style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
          ),
          Text(
            '${store.qaScore.toInt()}%',
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: AppColors.forestGreen,
            ),
          ),
          const SizedBox(width: 4),
          const Icon(Icons.check_circle, color: AppColors.forestGreen, size: 14),
        ],
      ),
    );
  }

  Widget _buildActionText(StorefrontListItem store) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          const Text(
            'Action Required: ',
            style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
          ),
          Text(
            store.actionText!,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: AppColors.brown,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProgressInfo(StorefrontListItem store) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'VoiceFront AI is building your storefront layout based on your audio description...',
            style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: store.progress,
              backgroundColor: AppColors.cardBg,
              valueColor: const AlwaysStoppedAnimation<Color>(AppColors.brandBlue),
              minHeight: 6,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStoreButtons(StorefrontListItem store) {
    if (store.liveUrl != null) {
      return Row(
        children: [
          Expanded(
            child: _buildIconLabelButton(
              Icons.share_rounded,
              'Share',
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _buildIconLabelButton(
              Icons.link_rounded,
              'Copy Link',
            ),
          ),
        ],
      );
    }

    if (store.actionLabel != null) {
      return SizedBox(
        width: double.infinity,
        child: OutlinedButton(
          onPressed: () {},
          style: OutlinedButton.styleFrom(
            side: const BorderSide(color: AppColors.brandBlue),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
            padding: const EdgeInsets.symmetric(vertical: 12),
          ),
          child: Text(
            store.actionLabel!,
            style: const TextStyle(
              color: AppColors.brandBlue,
              fontWeight: FontWeight.w600,
              fontSize: 14,
            ),
          ),
        ),
      );
    }

    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: null,
        icon: const Icon(Icons.hourglass_empty_rounded, size: 18),
        label: const Text(
          'Please Wait',
          style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.grey,
          disabledBackgroundColor: AppColors.grey,
          foregroundColor: AppColors.white,
          disabledForegroundColor: AppColors.white,
          padding: const EdgeInsets.symmetric(vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          elevation: 0,
        ),
      ),
    );
  }

  Widget _buildIconLabelButton(IconData icon, String label) {
    return OutlinedButton.icon(
      onPressed: () {},
      icon: Icon(icon, size: 18, color: AppColors.brandBlue),
      label: Text(
        label,
        style: const TextStyle(
          color: AppColors.brandBlue,
          fontWeight: FontWeight.w600,
          fontSize: 13,
        ),
      ),
      style: OutlinedButton.styleFrom(
        side: const BorderSide(color: AppColors.brandBlue),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        padding: const EdgeInsets.symmetric(vertical: 10),
      ),
    );
  }
}
