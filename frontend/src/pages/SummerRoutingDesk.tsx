import React from 'react';
import QueueDesk from '@/components/QueueDesk';

const SummerRoutingDesk = () => {
  return (
    <QueueDesk 
      title="Routage École d'Été"
      endpoint="/students/queues/summer"
      actionLabel="Assigner École d'Été"
      actionType="RESOLVE_REVIEW"
      emptyMessage="Aucun dossier en attente de routage école d'été"
    />
  );
};

export default SummerRoutingDesk;
