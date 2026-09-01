class CategoryItem {
  final String icon;
  final String name;
  final String hindi;

  const CategoryItem({required this.icon, required this.name, required this.hindi});
}

const List<CategoryItem> categories = [
  CategoryItem(icon: '🍽️', name: 'Food', hindi: 'भोजन'),
  CategoryItem(icon: '👕', name: 'Apparel', hindi: 'परिधान'),
  CategoryItem(icon: '📱', name: 'Electronics', hindi: 'इलेक्ट्रॉनिक्स'),
  CategoryItem(icon: '💊', name: 'Pharmacy', hindi: 'फार्मेसी'),
  CategoryItem(icon: '🔧', name: 'Services', hindi: 'सेवाएं'),
];

class RecentStorefront {
  final String name;
  final String icon;
  final String status;
  final int colorValue;

  const RecentStorefront({
    required this.name,
    required this.icon,
    required this.status,
    required this.colorValue,
  });
}

const List<RecentStorefront> recentStorefronts = [
  RecentStorefront(
    name: "Raju's Chaat Corner",
    icon: '🍽️',
    status: 'Active',
    colorValue: 0xFFF59E0B,
  ),
  RecentStorefront(
    name: 'Kavita Boutique',
    icon: '👗',
    status: 'Active',
    colorValue: 0xFFEC4899,
  ),
];

class ProductItem {
  final String name;
  final double? price;
  final bool hasError;

  const ProductItem({required this.name, this.price, this.hasError = false});
}

class StorefrontListItem {
  final String name;
  final String icon;
  final String status;
  final double qaScore;
  final String? liveUrl;
  final String? actionText;
  final String? actionLabel;
  final double? progress;
  final int statusColorValue;

  const StorefrontListItem({
    required this.name,
    required this.icon,
    required this.status,
    required this.qaScore,
    this.liveUrl,
    this.actionText,
    this.actionLabel,
    this.progress,
    required this.statusColorValue,
  });
}

const List<StorefrontListItem> storefrontList = [
  StorefrontListItem(
    name: 'Krishna Sweets',
    icon: '🏪',
    status: 'PUBLISHED',
    qaScore: 99,
    liveUrl: 'vfront.in/krishna',
    statusColorValue: 0xFF16A34A,
  ),
  StorefrontListItem(
    name: 'Jaipur Services',
    icon: '🔧',
    status: 'REPAIRED',
    qaScore: 95,
    actionText: 'Review fixes',
    actionLabel: 'Review Changes',
    statusColorValue: 0xFFD97706,
  ),
  StorefrontListItem(
    name: 'Mobile Hub',
    icon: '⏳',
    status: 'PROCESSING...',
    qaScore: 0,
    progress: 0.7,
    statusColorValue: 0xFF9CA3AF,
  ),
];
