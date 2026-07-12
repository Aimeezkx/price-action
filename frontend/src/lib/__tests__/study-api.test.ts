import { beforeEach, describe, expect, it, vi } from 'vitest';

import { apiClient } from '../api';


const jsonResponse = (data: unknown) =>
  new Response(JSON.stringify(data), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });


describe('study API contract', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  it('unwraps the card collection returned by the backend', async () => {
    vi.mocked(global.fetch).mockResolvedValue(
      jsonResponse({ total_cards: 1, cards: [{ id: 'card-1', front: 'Q', back: 'A' }] }),
    );

    const cards = await apiClient.getCards();

    expect(cards).toHaveLength(1);
    expect(cards[0].id).toBe('card-1');
  });

  it('maps review card IDs and uses the direct grade endpoint', async () => {
    vi.mocked(global.fetch)
      .mockResolvedValueOnce(
        jsonResponse([{ card_id: 'card-2', front: 'Q', back: 'A', card_type: 'qa' }]),
      )
      .mockResolvedValueOnce(jsonResponse({ success: true }));

    const cards = await apiClient.getTodayReview();
    await apiClient.gradeCard(cards[0].id, 4);

    expect(cards[0].id).toBe('card-2');
    expect(global.fetch).toHaveBeenLastCalledWith(
      '/api/reviews/cards/card-2/grade',
      expect.objectContaining({ method: 'POST', body: JSON.stringify({ grade: 4 }) }),
    );
  });
});
