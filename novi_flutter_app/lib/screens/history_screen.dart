import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/sorting_event.dart';
import '../services/firebase_service.dart';
import '../theme/app_theme.dart';
import '../widgets/common_widgets.dart';
import '../widgets/event_card.dart';

class HistoryScreen extends StatefulWidget {
  final FirebaseService firebase;

  const HistoryScreen({super.key, required this.firebase});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  String _selectedCategory = 'ALL';
  String _selectedFeedback = 'ALL';
  String _searchQuery = '';
  final TextEditingController _searchCtrl = TextEditingController();

  final List<String> _categories = [
    'ALL',
    'BIODEGRADABLE',
    'PLASTIC',
    'METAL',
    'OTHER',
  ];

  final List<String> _feedbackOptions = [
    'ALL',
    'PENDING',
    'CORRECT',
    'INCORRECT',
  ];

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  void _exportData(List<SortingEvent> events) {
    final csv = SorterStats.exportToCsv(events);
    Clipboard.setData(ClipboardData(text: csv));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Copied ${events.length} records in CSV format to clipboard!'),
        backgroundColor: AppTheme.primaryGreenDark,
        action: SnackBarAction(
          label: 'OK',
          textColor: Colors.white,
          onPressed: () {},
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return StreamBuilder<List<SortingEvent>>(
      stream: widget.firebase.eventsStream(),
      builder: (context, snap) {
        final allEvents = snap.data ?? [];

        // Apply filters
        final filteredEvents = allEvents.where((e) {
          // Category filter
          if (_selectedCategory != 'ALL') {
            final cat = (e.detectedClass ?? e.selectedBin ?? '').toUpperCase();
            if (cat != _selectedCategory) return false;
          }

          // Feedback filter
          if (_selectedFeedback != 'ALL') {
            if (e.feedbackStatus.toUpperCase() != _selectedFeedback) return false;
          }

          // Search query
          if (_searchQuery.isNotEmpty) {
            final q = _searchQuery.toLowerCase();
            final matchesId = e.eventId.toLowerCase().contains(q);
            final matchesClass = (e.detectedClass ?? '').toLowerCase().contains(q);
            final matchesBin = (e.selectedBin ?? '').toLowerCase().contains(q);
            if (!matchesId && !matchesClass && !matchesBin) return false;
          }

          return true;
        }).toList();

        return Scaffold(
          appBar: AppBar(
            backgroundColor: isDark ? AppTheme.darkBg : const Color(0xFFF8FAFC),
            elevation: 0,
            title: const Text('Sorting History', style: TextStyle(fontWeight: FontWeight.bold)),
            actions: [
              IconButton(
                tooltip: 'Export CSV',
                icon: const Icon(Icons.download_rounded),
                onPressed: allEvents.isEmpty ? null : () => _exportData(filteredEvents),
              ),
              const SizedBox(width: 8),
            ],
          ),
          body: Column(
            children: [
              // Search & Filter header
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: TextField(
                  controller: _searchCtrl,
                  onChanged: (val) => setState(() => _searchQuery = val.trim()),
                  decoration: InputDecoration(
                    hintText: 'Search by ID or Category...',
                    prefixIcon: const Icon(Icons.search, size: 20),
                    suffixIcon: _searchQuery.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, size: 18),
                            onPressed: () {
                              _searchCtrl.clear();
                              setState(() => _searchQuery = '');
                            },
                          )
                        : null,
                    contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                  ),
                ),
              ),

              // Category Filter Pills
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                child: Row(
                  children: _categories.map((cat) {
                    final isSelected = _selectedCategory == cat;
                    final catColor = cat == 'ALL' ? AppTheme.primaryGreen : AppTheme.getCategoryColor(cat);
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: FilterChip(
                        label: Text(cat),
                        selected: isSelected,
                        onSelected: (selected) {
                          setState(() => _selectedCategory = cat);
                        },
                        selectedColor: catColor.withValues(alpha: 0.25),
                        checkmarkColor: catColor,
                        labelStyle: TextStyle(
                          fontSize: 11,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                          color: isSelected
                              ? catColor
                              : (isDark ? Colors.white70 : Colors.black87),
                        ),
                        side: BorderSide(
                          color: isSelected ? catColor : (isDark ? AppTheme.darkBorder : const Color(0xFFE2E8F0)),
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ),

              // Feedback status pills & Count row
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                child: Row(
                  children: [
                    Text(
                      '${filteredEvents.length} of ${allEvents.length} items',
                      style: TextStyle(
                        fontSize: 12,
                        color: isDark ? Colors.white60 : Colors.black54,
                      ),
                    ),
                    const Spacer(),
                    // Feedback Filter Dropdown
                    PopupMenuButton<String>(
                      initialValue: _selectedFeedback,
                      tooltip: 'Filter by Feedback',
                      onSelected: (val) => setState(() => _selectedFeedback = val),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: isDark ? AppTheme.darkCard : const Color(0xFFF1F5F9),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              'Feedback: $_selectedFeedback',
                              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
                            ),
                            const SizedBox(width: 4),
                            const Icon(Icons.arrow_drop_down, size: 16),
                          ],
                        ),
                      ),
                      itemBuilder: (_) => _feedbackOptions
                          .map((f) => PopupMenuItem(value: f, child: Text(f)))
                          .toList(),
                    ),
                  ],
                ),
              ),

              const Divider(height: 1),

              // Events List
              Expanded(
                child: filteredEvents.isEmpty
                    ? EmptyStateWidget(
                        icon: Icons.history_toggle_off,
                        title: 'No matching records',
                        subtitle: allEvents.isEmpty
                            ? 'As Novi classifies items, sorting logs will be recorded here.'
                            : 'Try adjusting your search query or filter chips.',
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        itemCount: filteredEvents.length,
                        itemBuilder: (context, index) {
                          final event = filteredEvents[index];
                          return EventCard(
                            event: event,
                            firebase: widget.firebase,
                            onFeedbackSubmitted: () => setState(() {}),
                          );
                        },
                      ),
              ),
            ],
          ),
        );
      },
    );
  }
}
