import React from 'react';
import QueueDesk from '@/components/QueueDesk';

const IfpDesk = () => {
  return (
    <QueueDesk 
      title="Bureau IFP"
      endpoint="/students/queues/ifp"
      actionLabel="Valider Candidature"
      actionType="RESOLVE_REVIEW"
      emptyMessage="Bureau propre : Aucun dossier en attente de révision IFP"
    />
  );
};

export default IfpDesk;
