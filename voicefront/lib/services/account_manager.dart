import 'package:flutter/material.dart';

class AccountManager {
  static String userName = "Alex Morgan";
  static String userEmail = "alex@voicefront.ai";
  static String userPlan = "VF Enterprise Pro";
  static List<Map<String, dynamic>> savedArtifacts = [
    {
      "id": "vf_art_001",
      "name": "Gourmet Kitchen & Cafe",
      "category": "food",
      "timestamp": "2026-10-17 14:30",
      "status": "Published"
    },
    {
      "id": "vf_art_002",
      "name": "Rock & Melody Instruments",
      "category": "services",
      "timestamp": "2026-10-17 15:10",
      "status": "Draft"
    }
  ];

  static void addArtifact(String name, String category) {
    savedArtifacts.insert(0, {
      "id": "vf_art_00${savedArtifacts.length + 1}",
      "name": name,
      "category": category,
      "timestamp": DateTime.now().toString().substring(0, 16),
      "status": "Published"
    });
  }
}
