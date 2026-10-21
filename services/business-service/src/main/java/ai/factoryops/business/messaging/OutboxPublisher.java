package ai.factoryops.business.messaging;

import ai.factoryops.business.repository.Repositories.OutboxRepository;
import jakarta.transaction.Transactional;
import org.springframework.amqp.core.*;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import java.time.Instant;

@Configuration class RabbitConfig {
  @Bean TopicExchange factoryOpsExchange(@Value("${factoryops.outbox.exchange}") String name){return new TopicExchange(name,true,false);}
  @Bean Queue agentQueue(){return QueueBuilder.durable("factoryops.agent.events").build();}
  @Bean Binding binding(Queue agentQueue,TopicExchange factoryOpsExchange){return BindingBuilder.bind(agentQueue).to(factoryOpsExchange).with("#");}
}
@Component
public class OutboxPublisher {
  private final OutboxRepository repo; private final RabbitTemplate rabbit; private final String exchange;
  public OutboxPublisher(OutboxRepository repo,RabbitTemplate rabbit,@Value("${factoryops.outbox.exchange}") String exchange){this.repo=repo;this.rabbit=rabbit;this.exchange=exchange;}
  @Scheduled(fixedDelayString="${factoryops.outbox.poll-ms:1000}") @Transactional
  public void publish(){ for(var e:repo.findTop50ByPublishedAtIsNullOrderByCreatedAtAsc()){ rabbit.convertAndSend(exchange,e.eventType,e.payload); e.publishedAt=Instant.now(); repo.save(e); } }
}
