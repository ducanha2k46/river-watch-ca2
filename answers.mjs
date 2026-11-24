export function studyAnswer(history) {
    const highest = Math.max(...history.map(row => row.total_events));
    const leaders = history.filter(row => row.total_events === highest);
    const descriptions = leaders.map(row => `${row.town}: ${row.total_events} winter high-flow events. First four winters ${row.first_four}; last four ${row.last_four}. ${row.last_four > row.first_four ? 'The last four had more events.' : 'The last four did not have more events.'}`);
    return 'Provisional study priority\n' + descriptions.join('\n') + '\nEvents are consecutive-day runs at or above each town\'s own P99, within October–March, 2016/17–2024/25. Counts do not establish damage, event duration, existing defences or the best engineering solution. Model-cell river identity remains uncertain.';
}
